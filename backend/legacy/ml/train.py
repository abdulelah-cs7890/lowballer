"""Train the used-car valuation model.

Run from the `backend/` directory:

    python -m legacy.ml.train

Loads the dataset (real Kaggle CSV if present, else synthetic), trains an XGBoost
regressor on log-price, evaluates on a held-out split, and writes the model + metrics
to `legacy/ml/artifacts/`. (Archived Haraj-era pipeline; the live eBay app doesn't load these.)
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

from legacy.valuation.features import TARGET, build_preprocessor, prepare_features
from legacy.ml.data_loader import load_dataset

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
SEED = 42


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    ape = np.abs((y_true - y_pred) / y_true)
    return {
        "mae": round(float(mae), 2),
        "rmse": round(rmse, 2),
        "r2": round(float(r2_score(y_true, y_pred)), 4),
        "mape": round(float(np.mean(ape)), 4),
        "median_ape": round(float(np.median(ape)), 4),
    }


def train() -> dict:
    df, source = load_dataset()
    y = df[TARGET].to_numpy(dtype=float)
    X = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED
    )

    # log-price target tames the right-skewed price distribution -> better % error
    model = TransformedTargetRegressor(
        regressor=Pipeline(
            steps=[
                ("prep", build_preprocessor()),
                (
                    "model",
                    XGBRegressor(
                        n_estimators=700,
                        max_depth=6,
                        learning_rate=0.05,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        min_child_weight=3,
                        random_state=SEED,
                        n_jobs=-1,
                        objective="reg:squarederror",
                    ),
                ),
            ]
        ),
        func=np.log1p,
        inverse_func=np.expm1,
    )

    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    metrics = _metrics(y_test, preds)
    metrics.update(
        source=source,
        n_train=int(len(X_train)),
        n_test=int(len(X_test)),
        target=TARGET,
    )

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACT_DIR / "model.joblib")
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    # keep the test split + predictions for the deeper evaluate.py report
    test_out = X_test.copy()
    test_out["actual_price"] = y_test
    test_out["predicted_price"] = preds
    test_out.to_csv(ARTIFACT_DIR / "test_predictions.csv", index=False)

    print(f"\nTrained on {source} data ({metrics['n_train']:,} train / {metrics['n_test']:,} test)")
    print(f"  MAE        : {metrics['mae']:>12,.0f} SAR")
    print(f"  RMSE       : {metrics['rmse']:>12,.0f} SAR")
    print(f"  R^2        : {metrics['r2']:>12.3f}")
    print(f"  MAPE       : {metrics['mape']*100:>11.1f}%")
    print(f"  Median APE : {metrics['median_ape']*100:>11.1f}%")
    print(f"\nSaved -> {ARTIFACT_DIR/'model.joblib'}")
    return metrics


if __name__ == "__main__":
    train()
