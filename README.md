<div align="center">

# 💸 Lowballer

### A real-time marketplace **mispricing detector**

Pulls real listings, prices each item against its comparables, and surfaces the
underpriced ones — **live**, **bilingual (AR / EN + RTL)**, in a dark dashboard.

![Python](https://img.shields.io/badge/Python_3.11-3776AB?logo=python&logoColor=white&style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&style=flat-square)
![Next.js](https://img.shields.io/badge/Next.js_15-000?logo=nextdotjs&logoColor=white&style=flat-square)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white&style=flat-square)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?logo=tailwindcss&logoColor=white&style=flat-square)
![eBay API](https://img.shields.io/badge/eBay_Browse_API-0064D2?logo=ebay&logoColor=white&style=flat-square)
![tests](https://img.shields.io/badge/tests-18_passing-3FB950?style=flat-square)

<img src="docs/screenshots/ebay-dashboard-en.png" alt="Lowballer dashboard" width="880">

</div>

---

## ⚡ What it is

Lowballer runs on **eBay electronics** (GPUs · phones · consoles · laptops) via the official
eBay API. For each item it computes a **fair value = the median of comparable same-model
listings**, then flags anything priced well below it.

> 💡 **Example** — a *Gigabyte RTX 4080 Super* listed at **\$880** when comparable cards sell
> for a **\$1,280** median (**~31 % below**) gets flagged and streams onto the dashboard live.

| Step | What happens |
|---|---|
| **1 · Pull** | real priced listings via the **eBay Browse API** (a watchlist of exact models) |
| **2 · Value** | median of same-model comps, outlier-trimmed |
| **3 · Filter** | category + relevance + condition rules drop accessories / broken / locked / wrong-variant — *cheap-for-a-reason ≠ a deal* |
| **4 · Serve** | flagged deals in a **real-time (SSE)** dashboard, fully **bilingual**, with the comps behind each price |

---

## 🖼️ Screenshots

**Arabic (RTL)** — the entire layout mirrors and every string is translated:

<img src="docs/screenshots/ebay-dashboard-ar.png" alt="Arabic RTL dashboard" width="880">

**Deal detail** — the fair value, the comparable listings it's based on, and a link to the real eBay item:

<img src="docs/screenshots/ebay-detail-en.png" alt="Deal detail with comps" width="880">

---

## 🔀 The pivot: Haraj → eBay &nbsp;·&nbsp; *the interesting part*

The most telling part of this project is **why the data source changed.**

**Attempt 1 — Haraj (Saudi used cars).** Built the whole thing: an ML valuation model on
real Saudi sale prices **and** a scraper that **reverse-engineers Haraj's React-Router
"turbo-stream"** to recover structured price/specs (Haraj client-side-renders, so the data
isn't in the HTML). Then measured the catch: **~99 % of Haraj listings publish no price** —
sellers negotiate in chat. A live 900-listing scan turned up **2 priced cars**. You can't
flag underpricing without a price.

**Attempt 2 — eBay (electronics).** Every listing has a price *plus* exact-model search →
clean comparables. Scraping is blocked by anti-bot, so Lowballer uses the **official Browse
API**, and valuation becomes a **comps-median**. The new hard problem is **noise** — the
cheapest listings are usually defective / locked / wrong-variant, so most of the work is
separating real deals from cheap-for-a-reason.

> Real engineering **plus** the judgment to drop a thesis the data didn't support.

<details>
<summary><b>🧠 The Haraj era — deep dive (ML model · backtest · Arabic NLP)</b></summary>

<br>

**Valuation model** — XGBoost on log-price, trained on the
[Saudi Arabia Used Cars dataset](https://www.kaggle.com/datasets/turkibintalib/saudi-arabia-used-cars-dataset)
(5,389 cleaned listings). Honest, domain-typical accuracy:

| Metric | Value |
|---|---|
| MAE | ~11,800 SAR |
| R² | 0.89 |
| MAPE | 16.6 % (median 10.6 %) |

<img src="backend/ml/artifacts/feature_importance.png" alt="Feature importance" width="560">

**Mispricing-detector backtest** — a good model isn't enough; the flag rule must catch real
deals without false alarms:

| Threshold | Precision | Recall | F1 |
|---|---|---|---|
| 10 % | 0.73 | 0.83 | 0.78 |
| **12 % (default)** | **0.75** | **0.82** | **0.78** |
| 15 % | 0.77 | 0.77 | 0.77 |
| 20 % | 0.83 | 0.68 | 0.74 |

12 % is the best-F1 operating point; a 45 % discount trips a *"needs review"* scam guard.

<img src="backend/ml/artifacts/pr_curve.png" alt="Precision-recall curve" width="460">

**Arabic normalizer** — `app/scraper/normalize.py` turns unstructured Arabic prose:

```
تويوتا كامري موديل ٢٠١٩ ماشي ٩٠ الف نظيفه وارد اوتوماتيك السعر ٦٨٠٠٠
```

into structured features:

```json
{ "make": "Toyota", "model": "Camry", "year": 2019, "mileage_km": 90000,
  "gear_type": "Automatic", "origin": "Imported", "price": 68000 }
```

handling Arabic-Indic digits (٩٠ → 90), the "الف" thousands unit, bilingual make/model
dictionaries, and gear / fuel / origin keywords.

</details>

---

## 🏗️ Architecture

```
eBay Browse API ─▶ comps-median + noise filter ─▶ flag ─▶ DB (SQLite/Postgres) ─▶ FastAPI ─▶ Next.js
                                                            │
                                                            └─▶ SSE ─▶ live "new deals" feed
```

The Haraj-era pipeline (scrape → turbo-stream parse → normalize → ML value) is documented in
[`docs/architecture.md`](docs/architecture.md).

---

## 🧰 Tech stack

| Layer | Tech |
|---|---|
| **Frontend** | Next.js 15 · TypeScript · Tailwind · next-intl (AR/EN + RTL) · SSE client |
| **Backend** | FastAPI · eBay Browse API · comps-median valuation · SQLAlchemy (SQLite → Supabase Postgres) |
| **Haraj era** | XGBoost · scikit-learn · a React-Router turbo-stream scraper |

---

## 🚀 Getting started

```bash
# backend
cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt

# eBay deals (the live product) — put free keys in backend/.env first:
#   EBAY_CLIENT_ID / EBAY_CLIENT_SECRET   (from developer.ebay.com)
.venv/Scripts/python -m app.ebay.check "RTX 4090"      # smoke-test the API
.venv/Scripts/python -m app.ebay.ingest                # real deals into the DB
.venv/Scripts/python -m uvicorn app.main:app --reload  # :8000

# frontend
cd ../frontend && npm install && npm run dev           # http://localhost:3000
```

> The Haraj-era ML pipeline runs with **no accounts**:
> `python -m ml.train && python -m ml.evaluate && python -m ml.backtest`

Tests: `cd backend && .venv/Scripts/python -m pytest -q` &nbsp;→&nbsp; **18 passing**

---

## 📍 Status

- ✅ **eBay electronics deal-finder** — live: real Browse-API data · comps valuation + noise filtering · product UI · realtime SSE · AR/EN RTL
- ✅ **Haraj era (in repo)** — ML valuation model (real Saudi data, backtested) · turbo-stream scraper · the price-availability finding that drove the pivot
- ⬜ **Deferred** — Telegram alerts · auth / saved searches · cloud deploy (wired, pending accounts)
