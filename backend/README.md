# Lowballer — backend

FastAPI service for the **live eBay electronics deal-finder**: pull listings via the eBay
Browse API → value each against its same-model comps (outlier-trimmed median) → flag the
underpriced ones → serve them to the dashboard, with new deals streaming over SSE.

> The original Haraj-era car pipeline (ML valuation model + scraper) is archived under
> [`legacy/`](legacy) — see [legacy/README.md](legacy/README.md). It isn't imported here and is
> excluded from CI.

## Setup

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-api.txt   # live app: slim deps
# requirements.txt instead if you also want to run the legacy ML pipeline
```

The live path is pure FastAPI + SQLAlchemy + httpx — **no ML/data stack** (scikit-learn,
numpy, pandas, joblib live only in the archived `legacy/` pipeline).

## Run

```bash
# put free eBay keys in backend/.env first (from developer.ebay.com):
#   EBAY_CLIENT_ID / EBAY_CLIENT_SECRET
python -m app.ebay.check "RTX 4090"        # smoke-test the Browse API
python -m app.ebay.ingest                  # initial load: search → median → flag → DB
python -m uvicorn app.main:app --reload    # http://localhost:8000
python -m app.ebay.scheduler               # keep deals fresh; new ones stream to the site
```

## How valuation works

For each watched model (`app/ebay/ingest.py: WATCHLIST`) Lowballer searches eBay, drops
accessories / broken / locked / wrong-variant listings (category + include/exclude tokens +
`JUNK_MARKERS`), then takes the **trimmed median of the comps** as fair value. A listing
meaningfully below it is flagged; an *absurd* discount trips a `needs_review` guard
(`app/ebay/valuation.py`). The refresh is **idempotent** — one open flag per listing — so
re-runs don't re-notify.

## Endpoints

`GET /healthz`, `GET /deals` (filters: `make`, `min_price`, `max_price`, `min_percent_below`),
`GET /deals/{id}` (details + the comps behind the price), `GET /deals/stream` (SSE: each
newly-flagged deal). Storage is SQLAlchemy over `DATABASE_URL` — SQLite locally, Supabase
Postgres in prod. Tables are created on startup via `init_db()`.

## Tests

```bash
python -m pytest -q          # 9 live tests (tests/) — what CI runs
pytest legacy/tests          # 15 more: the archived Haraj normalizer / parser / ML schema
```

## Layout

```
app/ebay/        Browse API client, comps-median valuation, ingest + refresh, scheduler
app/pricing.py   the Valuation primitive + flag threshold (no ML deps)
app/repository.py data access: list/get deals, idempotent upsert_deal, comps
app/models/      SQLAlchemy tables + Pydantic response schemas
app/main.py      FastAPI app: /deals, /deals/{id}, /deals/stream (SSE), /healthz
legacy/          archived Haraj scraper + ML valuation pipeline (not on the live path)
```
