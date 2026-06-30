"""SPL (Structured Product Labeling) XML generation (spec §2.2, §6.1).

Produces a Form 5066 cosmetic facility-registration SPL document. This is a
faithful skeleton over the HL7 v3 (urn:hl7-org:v3) structure with the key
identifying elements; the exact code system values must be confirmed against
the FDA ESG NextGen / SPL implementation guide before production use.
"""

import uuid
from datetime import date
from xml.sax.saxutils import escape

from app.models.facility import Facility

# Stable namespace seed so the same facility yields the same document/set IDs.
_SPL_DOC_NS = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")

# Representative SPL document-type code for a cosmetic facility registration.
# TODO: confirm against the FDA SPL implementation guide for MoCRA.
_FACILITY_REG_CODE = "51725-0"
_LOINC_OID = "2.16.840.1.113883.6.1"
_FEI_OID = "2.16.840.1.113883.4.82"  # FDA establishment identifier root


def _doc_id(facility: Facility) -> str:
    return str(uuid.uuid5(_SPL_DOC_NS, f"doc:{facility.id}"))


def generate_facility_spl(facility: Facility, effective: date | None = None) -> str:
    """Render a Form 5066 facility-registration SPL XML string."""
    eff = (effective or date.today()).strftime("%Y%m%d")
    name = escape(facility.name_en or "")
    address = escape(facility.address_en or "")
    email = escape(facility.email or "")
    fei = escape(facility.fei or "")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<document xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <id root="{_doc_id(facility)}"/>
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
