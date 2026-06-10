"""Shared feature schema and engineering for the used-car valuation model.

Canonical (normalized) columns used everywhere downstream:

    make, model, year, mileage_km, engine_size, fuel_type, gear_type,
    origin, region, color, options   ->   price (target)

The scraper's job is to map messy Haraj listing text into this same schema, so that
a live listing and a training row look identical to the model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

# --- canonical schema ---------------------------------------------------------

TARGET = "price"

NUMERIC_FEATURES = ["year", "mileage_km", "engine_size"]
DERIVED_FEATURES = ["age", "log_mileage"]
CATEGORICAL_FEATURES = [
    "make",
    "model",
    "origin",
    "fuel_type",
    "gear_type",
    "region",
    "color",
    "options",
]

# order fed into the preprocessor
FEATURE_COLUMNS = NUMERIC_FEATURES + DERIVED_FEATURES + CATEGORICAL_FEATURES

# Reference year for the `age` feature. Kept fixed so training and serving agree
# regardless of when the model is run; bump when retraining on newer data.
REFERENCE_YEAR = 2025

# Maps the Kaggle "Saudi Arabia Used Cars" (Syarah) columns -> canonical names.
# Live scraped data is produced already-normalized, so it bypasses this map.
KAGGLE_COLUMN_MAP = {
    "Make": "make",
    "Type": "model",
    "Year": "year",
    "Origin": "origin",
    "Color": "color",
    "Options": "options",
    "Engine_Size": "engine_size",
    "Fuel_Type": "fuel_type",
    "Gear_Type": "gear_type",
    "Mileage": "mileage_km",
    "Region": "region",
    "Price": "price",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw dataset columns to the canonical schema (idempotent)."""
    renamed = df.rename(columns=KAGGLE_COLUMN_MAP)
    keep = [c for c in (FEATURE_COLUMNS + [TARGET]) if c in renamed.columns]
    # `age`/`log_mileage` are derived later, not expected in raw data
    keep = [c for c in keep if c not in DERIVED_FEATURES]
    return renamed[keep].copy()


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add model-ready derived columns. Safe to call on a single-row frame (serving)."""
    out = df.copy()
    out["age"] = (REFERENCE_YEAR - pd.to_numeric(out["year"], errors="coerce")).clip(lower=0)
    out["log_mileage"] = np.log1p(pd.to_numeric(out["mileage_km"], errors="coerce").clip(lower=0))
    # ensure every expected categorical exists, even if a listing was missing it
    for col in CATEGORICAL_FEATURES:
        if col not in out.columns:
            out[col] = "unknown"
        out[col] = out[col].fillna("unknown").astype(str)
    return out


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Full path from normalized data to the exact frame the model pipeline expects.

    Used identically by training and serving.
    """
    out = add_derived_features(df)
    return out[FEATURE_COLUMNS]


def build_preprocessor() -> ColumnTransformer:
    """One-hot encode categoricals; pass numerics through (trees need no scaling).

    `min_frequency` collapses rare categories (e.g. uncommon models) into a single
    bucket, keeping the matrix compact and robust to unseen values at serving time.
    """
    return ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUMERIC_FEATURES + DERIVED_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=10),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )
