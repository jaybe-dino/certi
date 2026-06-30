"""Seed INCI mapping dictionary: Korean / common name → INCI standard name.

A starter set for the mapping engine (spec FR-07). In production this is
backed by the INCI/CosIng DB with CIR/PCPC cross-references (spec §6.2);
here it is a curated seed sufficient for the matching logic and tests.
All keys are normalized (lowercase, stripped) by the engine before lookup.
"""

# Korean / common ingredient name → official INCI name.
INCI_DICTIONARY: dict[str, str] = {
    "정제수": "Water",
    "물": "Water",
    "워터": "Water",
    "글리세린": "Glycerin",
    "글리세롤": "Glycerin",
    "부틸렌글라이콜": "Butylene Glycol",
    "프로필렌글라이콜": "Propylene Glycol",
    "히알루론산": "Hyaluronic Acid",
    "소듐히알루로네이트": "Sodium Hyaluronate",
    "나이아신아마이드": "Niacinamide",
    "비타민b3": "Niacinamide",
    "판테놀": "Panthenol",
    "비타민b5": "Panthenol",
    "아데노신": "Adenosine",
    "알란토인": "Allantoin",
    "토코페롤": "Tocopherol",
    "비타민e": "Tocopherol",
    "아스코빅애씨드": "Ascorbic Acid",
    "비타민c": "Ascorbic Acid",
    "레티놀": "Retinol",
    "살리실릭애씨드": "Salicylic Acid",
    "시트릭애씨드": "Citric Acid",
    "다이메티콘": "Dimethicone",
    "스쿠알란": "Squalane",
    "시어버터": "Butyrospermum Parkii Butter",
    "병풀추출물": "Centella Asiatica Extract",
    "녹차추출물": "Camellia Sinensis Leaf Extract",
    "알로에베라": "Aloe Barbadensis Leaf Juice",
    "카프릴릭카프릭트라이글리세라이드": "Caprylic/Capric Triglyceride",
    "세틸알코올": "Cetyl Alcohol",
    "스테아릭애씨드": "Stearic Acid",
    "잔탄검": "Xanthan Gum",
    "카보머": "Carbomer",
    "페녹시에탄올": "Phenoxyethanol",
    "에탄올": "Alcohol",
    "티타늄디옥사이드": "Titanium Dioxide",
    "징크옥사이드": "Zinc Oxide",
    "향료": "Fragrance",
}
