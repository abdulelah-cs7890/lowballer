# Lowballer — backend

Python service: the **valuation model** (M1), the **API** (M2), and the **Haraj scraper**
(M3). Start with the ML pipeline — it runs with zero external accounts.

## Setup

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux
```

## M1 — train & evaluate the valuation model

```bash
python -m ml.train      # trains XGBoost, writes ml/artifacts/{model.joblib, metrics.json}
python -m ml.evaluate   # error-by-band report + feature-importance & scatter PNGs
```

By default this uses a **synthetic** Saudi-market dataset so it runs immediately. To train
on real prices, download the [Saudi Arabia Used Cars dataset](https://www.kaggle.com/datasets/turkibintalib/saudi-arabia-used-cars-dataset)
and save the CSV as `ml/data/saudi_used_cars.csv`, then re-run `python -m ml.train`. The
column mapping is already wired up (`app/valuation/features.py: KAGGLE_COLUMN_MAP`).

Artifacts land in `ml/artifacts/`:
- `model.joblib` — the fitted pipeline the API/worker loads
- `metrics.json` — MAE / RMSE / R² / MAPE
- `feature_importance.png`, `actual_vs_predicted.png` — for the README/portfolio

## Using the model

```python
from app.valuation.model import Valuator
v = Valuator()
v.value({"make": "Toyota", "model": "Camry", "year": 2019, "mileage_km": 90000,
         "engine_size": 2.5, "fuel_type": "Gas", "gear_type": "Automatic",
         "origin": "Saudi", "region": "Riyadh", "color": "White",
         "options": "Full", "price": 45000})
# -> Valuation(predicted_price=..., percent_below=..., is_flagged=True, ...)
```

## M2 — API

```bash
python -m app.seed                         # populate the dev DB with sample deals
python -m uvicorn app.main:app --reload     # http://localhost:8000
```
Endpoints: `GET /healthz`, `GET /deals` (filters: `make`, `min_price`, `max_price`,
`min_percent_below`), `GET /deals/{id}` (specs + comps). Storage is SQLAlchemy over
`DATABASE_URL` — SQLite locally, Supabase Postgres in prod (`supabase/schema.sql`).

## M3 — Haraj scraper + ingest worker

```bash
python -m app.worker        # ingest fixtures -> normalize -> value -> flag -> DB
```
Pipeline: `app/scraper/` does fetch (`client.py`, rate-limited + robots-aware), parse
(`parse.py`), and the core **Arabic→structured normalizer** (`normalize.py`, e.g.
`"تويوتا كامري ٢٠١٩ ماشي ٩٠ الف السعر ٣٨٠٠٠"` → `{make: Toyota, model: Camry, year: 2019,
mileage_km: 90000, price: 38000}`). The default source is offline fixtures
(`tests/fixtures/car_listings.json`); `live_haraj_source` fetches real listing URLs when
you're ready.

> Note: fixture asking prices are set ~14–17% below the trained model's fair value so the
> demo flags realistic deals (no scam-guard false positives).

## Tests

```bash
python -m pytest -q
```

## Layout

```
app/valuation/   feature schema (features.py) + inference & flag logic (model.py)
app/scraper/     Haraj scraper                        (M3)
app/main.py      FastAPI app                          (M2)
ml/              train.py, evaluate.py, synthetic + real data loaders
```
