"""Model inference + mispricing-flag logic.

Loads the trained sklearn Pipeline (preprocessor + XGBoost) and exposes the two
operations the live worker needs: predict a fair value, and decide whether a listing
is underpriced enough to flag.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

from .features import prepare_features

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "ml" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "model.joblib"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"

# A listing must be at least this far below predicted value to be flagged.
DEFAULT_FLAG_THRESHOLD = 0.12  # 12%
# Discounts larger than this are usually scams / salvage / wrong data, not deals.
SUSPICIOUS_DISCOUNT = 0.45  # 45%


@dataclass
class Valuation:
    asking_price: float
    predicted_price: float
    percent_below: float          # 0.13 == asking is 13% below predicted
    is_flagged: bool
    needs_review: bool            # too-good-to-be-true; surface but warn
    model_mae: float | None       # headline accuracy, for displaying confidence

    def to_dict(self) -> dict:
        return asdict(self)


class Valuator:
    """Wraps the trained pipeline. Construct once, reuse for every listing."""

    def __init__(self, model_path: Path = MODEL_PATH, metrics_path: Path = METRICS_PATH):
        if not model_path.exists():
            raise FileNotFoundError(
                f"No trained model at {model_path}. Run `python ml/train.py` first."
            )
        self.pipeline = joblib.load(model_path)
        self.mae: float | None = None
        if metrics_path.exists():
            self.mae = json.loads(metrics_path.read_text()).get("mae")

    def predict(self, records: Iterable[dict] | pd.DataFrame) -> np.ndarray:
        """Predict fair value for one or many normalized listings."""
        df = records if isinstance(records, pd.DataFrame) else pd.DataFrame(list(records))
        X = prepare_features(df)
        return np.asarray(self.pipeline.predict(X), dtype=float)

    def value(self, record: dict, threshold: float = DEFAULT_FLAG_THRESHOLD) -> Valuation:
        """Value a single listing and decide whether it's a flag-worthy deal."""
        predicted = float(self.predict([record])[0])
        asking = float(record["price"])
        percent_below = (predicted - asking) / predicted if predicted > 0 else 0.0
        return Valuation(
            asking_price=asking,
            predicted_price=round(predicted, 2),
            percent_below=round(percent_below, 4),
            is_flagged=percent_below >= threshold,
            needs_review=percent_below >= SUSPICIOUS_DISCOUNT,
            model_mae=self.mae,
        )
