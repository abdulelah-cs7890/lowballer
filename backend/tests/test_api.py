"""HTTP-level tests for the API endpoints (FastAPI TestClient over a temp DB)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import repository
from app.db import Base, get_session
from app.main import app
from app.pricing import Valuation


@pytest.fixture
def client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api.db'}", connect_args={"check_same_thread": False}
    )
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with TestSession() as s:
        deal = Valuation(800, 1200, 0.3333, is_flagged=True, needs_review=False)
        rec = {"make": "GPU", "model": "RTX 4090", "price": 800,
               "title": "NVIDIA RTX 4090 24GB", "image": "http://img/1", "condition": "Used"}
        repository.upsert_deal(s, "ebay-test-1", rec, deal, source="ebay", url="http://ebay/1", title=rec["title"])
        comp = Valuation(1150, 1200, 0.0417, is_flagged=False, needs_review=False)
        repository.upsert_deal(s, "ebay-test-2", {**rec, "price": 1150, "title": "ASUS RTX 4090"},
                               comp, source="ebay", url="http://ebay/2", title="ASUS RTX 4090")
        s.commit()

    def override_session():
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_deals_returns_product_fields(client):
    r = client.get("/deals?limit=10")
    assert r.status_code == 200
    deals = r.json()
    flagged = next(d for d in deals if d["id"] == "ebay-test-1")
    assert flagged["image"] and flagged["condition"] == "Used"
    assert flagged["percent_below"] > 0.3  # sorted/served as a real deal


def test_deal_detail_has_comps(client):
    r = client.get("/deals/ebay-test-1")
    assert r.status_code == 200
    body = r.json()
    assert body["title"] and isinstance(body["comps"], list)
    assert any((c.get("title") or "").startswith("ASUS") for c in body["comps"])


def test_missing_deal_404(client):
    assert client.get("/deals/does-not-exist").status_code == 404
