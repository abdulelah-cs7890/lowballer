"""Tests for the Arabic listing normalizer — the scraper's core."""

from __future__ import annotations

from legacy.scraper.normalize import (
    detect_make_model,
    extract_mileage,
    extract_price,
    extract_year,
    normalize_listing,
    _norm,
)


def test_make_model_arabic():
    assert detect_make_model(_norm("تويوتا كامري 2019")) == ("Toyota", "Camry")
    assert detect_make_model(_norm("نيسان باترول ديزل")) == ("Nissan", "Patrol")


def test_make_model_latin_scoped():
    # "LX" should resolve to Lexus LX, not collide with another brand
    assert detect_make_model(_norm("لكزس LX 2020")) == ("Lexus", "LX")


def test_year_prefers_model_keyword():
    assert extract_year(_norm("كامري موديل 2019 ماشي 2020 كم")) == 2019


def test_arabic_indic_digits():
    assert extract_year(_norm("موديل ٢٠١٨")) == 2018
    assert extract_mileage(_norm("ممشى ٩٠ الف")) == 90_000


def test_mileage_units():
    assert extract_mileage(_norm("ممشى 120 الف")) == 120_000
    assert extract_mileage(_norm("عداد 150000 كم")) == 150_000


def test_price_forms():
    assert extract_price(_norm("السعر ٤٥٠٠٠")) == 45_000
    assert extract_price(_norm("ب 90 الف")) == 90_000
    assert extract_price(_norm("38000 ريال")) == 38_000


def test_normalize_full_record():
    raw = {
        "id": "1",
        "url": "u",
        "title": "تويوتا كامري 2019 وارد",
        "body_text": "ماشي ٩٠ الف اوتوماتيك السعر ٤٥٠٠٠ الرياض",
    }
    rec = normalize_listing(raw)
    assert rec["make"] == "Toyota" and rec["model"] == "Camry"
    assert rec["year"] == 2019
    assert rec["mileage_km"] == 90_000
    assert rec["price"] == 45_000
    assert rec["gear_type"] == "Automatic"
    assert rec["origin"] == "Imported"
    assert rec["region"] == "Riyadh"
    assert rec["parse_confidence"] == 1.0


def test_normalize_rejects_low_signal():
    raw = {"id": "x", "url": "u", "title": "سيارة للبيع", "body_text": "بحالة ممتازة"}
    assert normalize_listing(raw) is None
