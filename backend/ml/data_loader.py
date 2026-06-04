"""Load training data: the real Kaggle CSV if present, else synthetic.

Real data: download the "Saudi Arabia Used Cars" dataset from Kaggle
(https://www.kaggle.com/datasets/turkibintalib/saudi-arabia-used-cars-dataset) and
save the CSV as `ml/data/saudi_used_cars.csv`. The loader normalizes its columns and
applies light cleaning. With no file present it falls back to a synthetic dataset of
the same schema so the pipeline always runs.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.valuation.features import TARGET, normalize_columns

DATA_DIR = Path(__file__).resolve().parent / "data"
REAL_CSV = DATA_DIR / "saudi_used_cars.csv"


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop unusable rows: missing/zero price, placeholder listings, absurd values."""
    df = df.copy()
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df["year"] = pd.to_numeric(df.get("year"), errors="coerce")
    df["mileage_km"] = pd.to_numeric(df.get("mileage_km"), errors="coerce")
    df["engine_size"] = pd.to_numeric(df.get("engine_size"), errors="coerce")
    df = df.dropna(subset=[TARGET, "year"])
    # On Syarah a price of 0/1 means "call for price", not a real value.
    df = df[(df[TARGET] >= 5_000) & (df[TARGET] <= 2_000_000)]
    df = df[(df["year"] >= 1990) & (df["year"] <= 2026)]
    df["mileage_km"] = df["mileage_km"].fillna(df["mileage_km"].median()).clip(0, 1_000_000)
    df["engine_size"] = df["engine_size"].fillna(df["engine_size"].median())
    return df.reset_index(drop=True)


def load_dataset(verbose: bool = True) -> tuple[pd.DataFrame, str]:
    """Return (cleaned normalized dataframe, source label)."""
    if REAL_CSV.exists():
        raw = pd.read_csv(REAL_CSV)
        df = _clean(normalize_columns(raw))
        if verbose:
            print(f"Loaded REAL dataset: {len(df):,} rows from {REAL_CSV.name}")
        return df, "kaggle_saudi"

    from .synth import make_synthetic_dataset

    df = _clean(make_synthetic_dataset())
    if verbose:
        print(
            f"No {REAL_CSV.name} found -> using SYNTHETIC dataset ({len(df):,} rows). "
            "Drop the Kaggle CSV in ml/data/ to train on real prices."
        )
    return df, "synthetic"
