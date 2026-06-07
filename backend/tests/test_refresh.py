"""Tests for the idempotent incremental refresh + Telegram no-op."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.ebay import ingest as ingest_mod
from app.models.tables import Flag

_FIX = json.loads((Path(__file__).parent / "fixtures" / "ebay_sample.json").read_text(encoding="utf-8"))
WATCHLIST = [
    ("GPU", "RTX 4090", "27386", ["4090"], []),
    ("Phone", "iPhone 15 Pro 256GB", "9355", ["iphone", "15 pro", "256"], ["max"]),
]


def _setup(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'refresh.db'}")
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(ingest_mod, "SessionLocal", TestSession)
    monkeypatch.setattr(ingest_mod, "init_db", lambda: None)
    return TestSession


def _make_search(fixture):
    return lambda query, category_id=None: list(fixture.get(query, []))


def _open_flags(TestSession):
    with TestSession() as s:
        return s.execute(select(Flag).where(Flag.status == "open")).scalars().all()


def test_refresh_is_idempotent(tmp_path, monkeypatch):
    TestSession = _setup(tmp_path, monkeypatch)
    search = _make_search(_FIX)

    first = ingest_mod.refresh(search, watchlist=WATCHLIST)
    assert len(first) >= 2  # genuine deals exist in the fixture
    flags_after_first = len(_open_flags(TestSession))

    second = ingest_mod.refresh(search, watchlist=WATCHLIST)
    assert second == []  # nothing newly flagged on a re-run
    assert len(_open_flags(TestSession)) == flags_after_first  # no duplicate flags

    ids = [f.listing_id for f in _open_flags(TestSession)]
    assert len(ids) == len(set(ids))  # at most one open flag per listing


def test_new_deal_detected_and_closed(tmp_path, monkeypatch):
    TestSession = _setup(tmp_path, monkeypatch)
    fixture = json.loads(json.dumps(_FIX))  # deep copy we can mutate
    search = _make_search(fixture)

    ingest_mod.refresh(search, watchlist=WATCHLIST)

    # a brand-new, clearly-underpriced RTX 4090 appears -> exactly one new deal
    fixture["RTX 4090"].append({
        "id": "v1|999|0", "title": "NVIDIA GeForce RTX 4090 24GB clean", "price": 900.0,
        "currency": "USD", "condition": "Used", "url": "https://www.ebay.com/itm/999",
        "image": None, "model": "RTX 4090",
    })
    new = ingest_mod.refresh(search, watchlist=WATCHLIST)
    assert any(d.get("url", "").endswith("/999") for d in new)

    # it disappears (sold/ended) -> its open flag is closed
    fixture["RTX 4090"] = [it for it in fixture["RTX 4090"] if it["id"] != "v1|999|0"]
    ingest_mod.refresh(search, watchlist=WATCHLIST)
    with TestSession() as s:
        gone = s.execute(
            select(Flag).where(Flag.listing_id == "ebay-v1|999|0", Flag.status == "open")
        ).scalar_one_or_none()
        assert gone is None
