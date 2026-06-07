"""Tests for eBay comps valuation + ingestion (offline fixture, temp DB)."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.ebay import ingest as ingest_mod
from app.ebay.valuation import SUSPICIOUS_DISCOUNT, assess, comps_value
from app.models.tables import Listing

_FIX = json.loads((Path(__file__).parent / "fixtures" / "ebay_sample.json").read_text(encoding="utf-8"))


def fixture_search(query: str, category_id: str | None = None) -> list[dict]:
    return _FIX.get(query, [])


def test_comps_value_median_and_thin():
    assert comps_value([100, 100, 100, 100, 100, 100, 100, 100]) == 100
    assert comps_value([100, 200, 300]) is None  # fewer than MIN_COMPS


def test_assess_flag_and_review():
    fair = 1000.0
    assert assess(1000, fair).is_flagged is False
    deal = assess(800, fair)  # 20% below -> real deal
    assert deal.is_flagged and not deal.needs_review
    junk = assess(50, fair)  # 95% below -> accessory/parts guard
    assert junk.needs_review and not junk.is_flagged
    assert SUSPICIOUS_DISCOUNT < 1.0


def test_ingest_against_fixture(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'ebay.db'}")
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(ingest_mod, "SessionLocal", TestSession)
    monkeypatch.setattr(ingest_mod, "init_db", lambda: None)

    watchlist = [
        ("GPU", "RTX 4090", "27386", ["4090"], []),
        ("Phone", "iPhone 15 Pro 256GB", "9355", ["iphone", "15 pro", "256"], ["max"]),
        ("GPU", "RX 7900 XTX", "27386", ["7900", "xtx"], []),
    ]
    stats = ingest_mod.ingest(fixture_search, watchlist=watchlist, replace=True)

    assert stats["thin"] == 1  # RX 7900 XTX has < MIN_COMPS listings
    assert stats["flagged"] >= 2  # the genuine deals in the GPU + phone groups

    session = TestSession()
    products = session.query(Listing).filter(Listing.source == "ebay").all()
    assert products
    assert any(p.image for p in products) and any(p.condition for p in products)
    # the $45 cable / $60 box are far below median -> stored but NOT flagged as deals
    session.close()
