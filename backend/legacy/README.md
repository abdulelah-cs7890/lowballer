# Legacy — the Haraj-era car pipeline (archived)

This is where Lowballer **started**: a used-car mispricing detector for [Haraj](https://haraj.com.sa)
(the Saudi classifieds marketplace), built around a trained ML valuation model. It's preserved
here, intact, because the **pivot from this to eBay is the project's story** (see the root README).

## Why it's archived, not deleted

While building the live scraper I measured that **~99% of Haraj car listings publish no price** —
sellers negotiate in chat — so there was almost nothing to value. The product pivoted to the
**eBay Browse API** (efficient market, exact-model search, real comps), which is the live app under
[`../app/`](../app/). This code is **not imported by the live app and is excluded from CI**, but it
still runs on its own.

## What's here

| Path | What it was |
|------|-------------|
| `scraper/` | Polite (rate-limited, robots-aware) Haraj client; HTML/OpenGraph parser; Arabic listing normalizer; React-Router data-stream field extractor. |
| `valuation/` | Shared feature schema + the `Valuator` (sklearn preprocessor + XGBoost) and flag logic. |
| `ml/` | Training pipeline (`train.py`), synthetic + Kaggle data loaders, backtest/evaluate, and saved `artifacts/` (model + metrics + plots). |
| `worker.py` | Offline pipeline: fixture source → normalize → value → flag → DB. |
| `scrape_live.py` | Harvest real priced car deals by walking back from the newest Haraj listing id. |
| `seed.py` | Seed the dev DB with synthetic valued/flagged cars. |
| `recorder.py` | `record_listing` persistence shared by the above (was `app.repository.record_listing`). |
| `tests/` | Unit tests for the normalizer, the HTML parser, and the valuation feature schema/flag logic. |

## Running it (optional)

Needs the ML stack (`scikit-learn`, `xgboost`, `numpy`, `pandas`, `joblib`) — see the root
`backend/requirements.txt`, not the slim `requirements-api.txt` the live API uses. From `backend/`:

```bash
python -m legacy.ml.train      # train the valuation model -> legacy/ml/artifacts/
python -m legacy.seed          # seed the dev DB with synthetic flagged cars
python -m legacy.worker        # ingest offline fixtures -> value -> flag -> DB
python -m legacy.scrape_live   # harvest real Haraj listings (slow; most have no price)
pytest legacy/tests            # run the archived unit tests
```

> Note: the current `Listing` model dropped its car-specific columns when the schema was cleaned
> for the product, so this code persists only the surviving fields (id/make/model/price/title/
> image/condition). The rich car attributes still flow through the in-memory record, which is all
> the `Valuator` needs to predict — so valuation and flagging behave as they did originally.
