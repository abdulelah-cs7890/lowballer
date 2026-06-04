# Architecture

## Overview

Lowballer is a two-source system. The **valuation model** is trained offline on a
clean dataset with real prices; the **live pipeline** scrapes messy Haraj listings,
normalizes them into the model's feature schema, values them, and flags the underpriced
ones into a database that the API and dashboard read.

```
   ┌──────────────────────────────┐
   │  TRAIN (offline, Python)      │
   │  Kaggle Saudi used-car data   │──▶ model.joblib  (XGBoost on log-price)
   │  feature eng → fit → evaluate │    + metrics.json + plots
   └──────────────────────────────┘
                                          │ loaded by
                                          ▼
 Haraj.sa ──▶ HarajClient ──▶ parse ──▶ normalize ──▶ Valuator.value() ──▶ flag?
 (SSR pages)  (robots+rate)   (HTML)   (Arabic→schema)  (predict + %below)   │
                                                                             ▼
                                            Postgres/SQLite: listings · valuations · flags
                                                          │
                              ┌───────────────────────────┼───────────────────────┐
                              ▼                            ▼                        ▼
                       FastAPI /deals          SSE /deals/stream (M4 ✓)    Telegram alerts (later)
                              │                            │
                              ▼                            ▼
                       Next.js dashboard (Vercel) ◀─ EventSource (live deals)
```

## Components

| Component | Path | Responsibility |
|---|---|---|
| Feature schema | `backend/app/valuation/features.py` | Canonical columns + preprocessing, shared by train & serve |
| Model + flag logic | `backend/app/valuation/model.py` | `Valuator`: predict fair value, decide flag / needs-review |
| Trainer | `backend/ml/train.py` | XGBoost on log-price → `model.joblib`, `metrics.json` |
| Evaluator / backtest | `backend/ml/evaluate.py`, `ml/backtest.py` | Error analysis, feature importance, detector precision/recall |
| Scraper client | `backend/app/scraper/client.py` | robots-aware, rate-limited, retrying HTTP |
| Parser | `backend/app/scraper/parse.py` | Haraj listing HTML → raw dict |
| **Normalizer** | `backend/app/scraper/normalize.py` | **Arabic free-text → structured features** |
| Worker | `backend/app/worker.py` | source → normalize → value → flag → DB |
| Data layer | `backend/app/repository.py`, `models/` | All DB access; storage-engine agnostic |
| API | `backend/app/main.py` | `/deals`, `/deals/{id}`, `/healthz` |
| Dashboard | `frontend/` | Next.js deal grid + detail/comps |

## Key decisions

- **Two data sources.** Training needs clean labels (real sale prices from Kaggle);
  the live market (Haraj) only has asking prices and messy text. Separating them lets us
  measure model accuracy honestly while still operating on live data.
- **One feature schema, imported by both train and serve** (`features.py`) so training
  and inference can never drift.
- **`DATABASE_URL` indirection** (SQLAlchemy) → SQLite in dev, Supabase Postgres in prod
  with no code change.
- **Parse the SSR pages, not the GraphQL API.** Haraj's GraphQL endpoint is WAF-protected
  (returns non-standard codes); listing pages render fine and are allowed by `robots.txt`.
- **`log1p` target.** Used-car prices are right-skewed; modeling log-price improves
  percentage error and keeps predictions positive.
- **Flag threshold = 12%**, chosen from the backtest's precision/recall curve (high recall,
  ~85% precision) with a 45% "needs review" guard for scam/salvage/data-error listings.
