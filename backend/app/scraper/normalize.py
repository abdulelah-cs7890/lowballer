"""Turn a raw Haraj listing (Arabic free-text title + body) into the canonical car
schema the valuation model expects.

This is the heart of the scraper: Haraj listings are unstructured Arabic prose like
    "تويوتا كامري ٢٠١٩ ماشي ٩٠ الف نظيفه وارد اوتوماتيك السعر ٥٥٠٠٠"
and we need {make: Toyota, model: Camry, year: 2019, mileage_km: 90000,
gear_type: Automatic, origin: Imported, price: 55000}.

Everything here is pure and fully unit-tested against fixtures — no network needed.
"""

from __future__ import annotations

import re

# --- Arabic make/model dictionary (aliases -> canonical), scoped to the model's vocab.
# Model lookups are scoped to a detected make, so short Latin tokens (ES, LX) can't
# cross-match other brands.
MAKES: dict[str, dict] = {
    "Toyota": {"aliases": ["تويوتا", "تيوتا", "toyota"], "models": {
        "Camry": ["كامري", "camry"], "Corolla": ["كورولا", "corolla"],
        "Land Cruiser": ["لاندكروزر", "لاند كروزر", "land cruiser", "lc"],
        "Hilux": ["هايلوكس", "hilux"], "Yaris": ["يارس", "yaris"]}},
    "Hyundai": {"aliases": ["هيونداي", "هونداي", "hyundai"], "models": {
        "Sonata": ["سوناتا", "sonata"], "Elantra": ["النترا", "إلنترا", "elantra"],
        "Accent": ["اكسنت", "accent"], "Tucson": ["توسان", "tucson"],
        "Azera": ["ازيرا", "azera"]}},
    "Ford": {"aliases": ["فورد", "ford"], "models": {
        "Taurus": ["تورس", "taurus"], "Explorer": ["اكسبلورر", "explorer"],
        "F-150": ["f-150", "f150", "اف 150"], "Edge": ["ايدج", "edge"],
        "Expedition": ["اكسبيديشن", "expedition"]}},
    "Nissan": {"aliases": ["نيسان", "nissan"], "models": {
        "Altima": ["التيما", "altima"], "Patrol": ["باترول", "patrol"],
        "Sunny": ["صني", "sunny"], "Xterra": ["اكستيرا", "xterra"],
        "Maxima": ["ماكسيما", "maxima"]}},
    "Lexus": {"aliases": ["لكزس", "lexus"], "models": {
        "ES": ["es"], "LX": ["lx"], "GX": ["gx"], "IS": ["is"], "RX": ["rx"]}},
    "Chevrolet": {"aliases": ["شفروليه", "شيفروليه", "chevrolet", "chevy"], "models": {
        "Tahoe": ["تاهو", "tahoe"], "Impala": ["امبالا", "impala"],
        "Silverado": ["سلفرادو", "silverado"], "Malibu": ["ماليبو", "malibu"],
        "Suburban": ["سوبربان", "suburban"]}},
    "Kia": {"aliases": ["كيا", "kia"], "models": {
        "Optima": ["اوبتيما", "optima"], "Cerato": ["سيراتو", "cerato"],
        "Sportage": ["سبورتاج", "sportage"], "Sorento": ["سورنتو", "sorento"],
        "Rio": ["ريو", "rio"]}},
    "GMC": {"aliases": ["جمس", "جي ام سي", "gmc"], "models": {
        "Yukon": ["يوكن", "yukon"], "Sierra": ["سييرا", "sierra"],
        "Acadia": ["اكاديا", "acadia"], "Terrain": ["ترين", "terrain"]}},
    "Honda": {"aliases": ["هوندا", "honda"], "models": {
        "Accord": ["اكورد", "accord"], "Civic": ["سيفيك", "civic"],
        "CR-V": ["cr-v", "crv", "سي ار في"], "Pilot": ["بايلوت", "pilot"]}},
    "Mercedes": {"aliases": ["مرسيدس", "مرسدس", "mercedes"], "models": {
        "C-Class": ["c-class", "c class", "سي كلاس"],
        "E-Class": ["e-class", "e class", "اي كلاس"],
        "S-Class": ["s-class", "s class", "اس كلاس"], "GLE": ["gle"]}},
}

_GEAR = {"Automatic": ["اوتوماتيك", "أوتوماتيك", "اتوماتيك", "اوتو", "automatic"],
         "Manual": ["قير عادي", "عادي", "مانيوال", "manual", "عاده"]}
_FUEL = {"Diesel": ["ديزل", "diesel"], "Hybrid": ["هايبرد", "هجين", "hybrid"],
         "Gas": ["بنزين", "gas", "gasoline"]}
_ORIGIN = {"Saudi": ["سعودي", "سعوديه", "سعودية", "وكالة", "وكاله"],
           "Gulf Arabic": ["خليجي", "خليجيه"], "Imported": ["وارد", "امريكي", "أمريكي"]}
_CITY_REGION = {"Riyadh": ["الرياض", "رياض"], "Jeddah": ["جده", "جدة"],
                "Dammam": ["الدمام", "دمام"], "Makkah": ["مكه", "مكة"],
                "Madinah": ["المدينه", "المدينة"], "Abha": ["ابها", "أبها"],
                "Tabuk": ["تبوك"]}

_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_THOUSAND = ("الف", "ألف", "آلاف", "k")


def _norm(text: str) -> str:
    """Normalize: arabic-indic digits -> western, unify alef/ya, drop tatweel, lower latin."""
    t = (text or "").translate(_AR_DIGITS)
    t = re.sub("[أإآا]", "ا", t)
    t = t.replace("ـ", "").replace("ى", "ي")
    return re.sub(r"\s+", " ", t).strip().lower()


def _first_alias(text: str, aliases: list[str]) -> int | None:
    """Earliest position any alias appears (word-bounded for latin tokens), else None."""
    best = None
    for a in aliases:
        a_l = _norm(a)  # match in the same normalized space as the text
        if a_l.isascii():
            m = re.search(rf"\b{re.escape(a_l)}\b", text)
            pos = m.start() if m else -1
        else:
            pos = text.find(a_l)
        if pos != -1 and (best is None or pos < best):
            best = pos
    return best


def detect_make_model(text: str) -> tuple[str | None, str | None]:
    make, make_pos = None, None
    for name, spec in MAKES.items():
        pos = _first_alias(text, spec["aliases"])
        if pos is not None and (make_pos is None or pos < make_pos):
            make, make_pos = name, pos
    if make is None:
        return None, None
    model, model_pos = None, None
    for mname, aliases in MAKES[make]["models"].items():
        pos = _first_alias(text, aliases)
        if pos is not None and (model_pos is None or pos < model_pos):
            model, model_pos = mname, pos
    return make, model


def extract_year(text: str) -> int | None:
    years = [int(y) for y in re.findall(r"(?<!\d)(19[89]\d|20[0-2]\d)(?!\d)", text)]
    years = [y for y in years if 1990 <= y <= 2026]
    if not years:
        return None
    # prefer a year right after "موديل/مديل/model"
    m = re.search(r"(?:موديل|مديل|model)\s*(19[89]\d|20[0-2]\d)", text)
    return int(m.group(1)) if m else years[0]


def _scaled(value: str, unit: str | None) -> int:
    n = float(value.replace(",", ""))
    if unit and any(u in unit for u in _THOUSAND):
        n *= 1000
    elif n < 1000:  # bare "90" almost always means 90 thousand for km/price
        n *= 1000
    return int(round(n))


def extract_mileage(text: str) -> int | None:
    # NOTE: patterns are written in _norm space (ى->ي, alef unified)
    pats = [
        r"(?:ممشي|الممشي|ماشي|مشت|مشي|عداد)\s*[:\-]?\s*([\d,]+)\s*(الف|الف|k|كم|كيلو)?",
        r"([\d,]+)\s*(الف|k)?\s*(?:كم|كيلو)",
    ]
    for p in pats:
        m = re.search(p, text)
        if m:
            km = _scaled(m.group(1), m.group(2))
            if 0 < km <= 1_000_000:
                return km
    return None


def extract_price(text: str) -> int | None:
    # NOTE: patterns are written in _norm space (ى->ي, alef unified)
    pats = [
        r"(?:السعر|سعر|المبلغ|بسعر|حد)\s*[:\-]?\s*([\d,]+)\s*(الف|k)?",
        r"(?:ب|علي)\s*([\d,]+)\s*(الف|k)\b",
        r"([\d,]+)\s*(الف)?\s*ريال",
    ]
    for p in pats:
        m = re.search(p, text)
        if m:
            price = _scaled(m.group(1), m.group(2) if m.lastindex and m.lastindex >= 2 else None)
            if 1000 <= price <= 5_000_000:
                return price
    return None


def _match_dict(text: str, mapping: dict[str, list[str]]) -> str | None:
    best, best_pos = None, None
    for canon, aliases in mapping.items():
        pos = _first_alias(text, aliases)
        if pos is not None and (best_pos is None or pos < best_pos):
            best, best_pos = canon, pos
    return best


def normalize_listing(raw: dict) -> dict | None:
    """raw: {id, url, title, body_text, price?, city?} -> canonical record (or None).

    Returns None only when there's not enough signal to value the car (no make or no
    year). The record always carries a `parse_confidence` in [0,1].
    """
    text = _norm(" ".join(filter(None, [raw.get("title"), raw.get("body_text")])))

    make, model = detect_make_model(text)
    year = extract_year(text)
    mileage = extract_mileage(text)
    price = raw.get("price") or extract_price(text)
    gear = _match_dict(text, _GEAR)
    fuel = _match_dict(text, _FUEL)
    origin = _match_dict(text, _ORIGIN)
    region = _match_dict(text, _CITY_REGION) or raw.get("city")

    if make is None or year is None or not price:
        return None  # can't value reliably

    extracted = [make is not None, model is not None, mileage is not None, price is not None]
    confidence = round(sum(extracted) / len(extracted), 2)

    return {
        "id": raw.get("id"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "make": make,
        "model": model,
        "year": year,
        # impute numerics the model needs but the listing omitted
        "mileage_km": mileage if mileage is not None else int(max(5_000, (2025 - year) * 18_000)),
        "engine_size": 2.5,
        "fuel_type": fuel,
        "gear_type": gear,
        "origin": origin,
        "region": region,
        "color": None,
        "options": None,
        "price": int(price),
        "parse_confidence": confidence,
    }
