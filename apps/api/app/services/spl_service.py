"""SPL (Structured Product Labeling) XML generation (spec §2.2, §6.1).

Produces a Form 5066 cosmetic facility-registration SPL document. This is a
faithful skeleton over the HL7 v3 (urn:hl7-org:v3) structure with the key
identifying elements; the exact code system values must be confirmed against
the FDA ESG NextGen / SPL implementation guide before production use.
"""

import uuid
from collections.abc import Sequence
from datetime import date
from xml.sax.saxutils import escape

from app.models.facility import Facility
from app.models.product import Ingredient, Product

# Stable namespace seed so the same facility yields the same document/set IDs.
_SPL_DOC_NS = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")

# Representative SPL document-type codes. TODO: confirm against the FDA SPL
# implementation guide for MoCRA before production use.
_FACILITY_REG_CODE = "51725-0"
_PRODUCT_LISTING_CODE = "51726-8"
_LOINC_OID = "2.16.840.1.113883.6.1"
_FEI_OID = "2.16.840.1.113883.4.82"  # FDA establishment identifier root


def _doc_id(entity_id: uuid.UUID) -> str:
    return str(uuid.uuid5(_SPL_DOC_NS, f"doc:{entity_id}"))


def generate_facility_spl(facility: Facility, effective: date | None = None) -> str:
    """Render a Form 5066 facility-registration SPL XML string."""
    eff = (effective or date.today()).strftime("%Y%m%d")
    name = escape(facility.name_en or "")
    address = escape(facility.address_en or "")
    email = escape(facility.email or "")
    fei = escape(facility.fei or "")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<document xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <id root="{_doc_id(facility.id)}"/>
  <code code="{_FACILITY_REG_CODE}" codeSystem="{_LOINC_OID}"
        displayName="Cosmetic Facility Registration"/>
  <title>Cosmetic Facility Registration (Form 5066)</title>
  <effectiveTime value="{eff}"/>
  <setId root="{facility.id}"/>
  <versionNumber value="1"/>
  <author>
    <assignedEntity>
      <representedOrganization>
        <id extension="{fei}" root="{_FEI_OID}"/>
        <name>{name}</name>
        <addr>{address}</addr>
        <telecom value="mailto:{email}"/>
      </representedOrganization>
    </assignedEntity>
  </author>
  <component>
    <structuredBody>
      <component>
        <section>
          <code code="48780-1" codeSystem="{_LOINC_OID}"
                displayName="Establishment Registration"/>
          <title>Establishment</title>
          <effectiveTime value="{eff}"/>
        </section>
      </component>
    </structuredBody>
  </component>
</document>
"""


def _ingredient_block(ingredients: Sequence[Ingredient]) -> str:
    rows = []
    for ing in ingredients:
        name = escape(ing.inci_name or ing.raw_name or "")
        rows.append(
            "          <ingredient>\n"
            f"            <ingredientSubstance><name>{name}</name></ingredientSubstance>\n"
            "          </ingredient>"
        )
    return "\n".join(rows)


def generate_product_spl(
    product: Product,
    ingredients: Sequence[Ingredient],
    facility_feis: Sequence[str],
    effective: date | None = None,
) -> str:
    """Render a Form 5067 cosmetic product-listing SPL XML string."""
    eff = (effective or date.today()).strftime("%Y%m%d")
    name = escape(product.name or "")
    category = escape(product.category or "")
    fei_block = "\n".join(
        f'        <id extension="{escape(fei)}" root="{_FEI_OID}"/>'
        for fei in facility_feis
        if fei
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<document xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <id root="{_doc_id(product.id)}"/>
  <code code="{_PRODUCT_LISTING_CODE}" codeSystem="{_LOINC_OID}"
        displayName="Cosmetic Product Listing"/>
  <title>Cosmetic Product Listing (Form 5067)</title>
  <effectiveTime value="{eff}"/>
  <setId root="{product.id}"/>
  <versionNumber value="1"/>
  <component>
    <structuredBody>
      <component>
        <section>
          <code code="48779-3" codeSystem="{_LOINC_OID}" displayName="Product Listing"/>
          <title>{name}</title>
          <text>Category: {category}</text>
          <effectiveTime value="{eff}"/>
{fei_block}
{_ingredient_block(ingredients)}
        </section>
      </component>
    </structuredBody>
  </component>
</document>
"""
