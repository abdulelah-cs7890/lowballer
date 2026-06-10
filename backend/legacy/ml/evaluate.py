"""Deeper evaluation report for the trained valuation model.

Run from `backend/` after training:

    python -m legacy.ml.evaluate

Reads the held-out predictions saved by train.py and produces:
  - a metrics recap + error-by-price-band breakdown (printed)
  - a feature-importance bar chart -> ml/artifacts/feature_importance.png
  - an actual-vs-predicted scatter -> ml/artifacts/actual_vs_predicted.png
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"


def _load():
    model = joblib.load(ARTIFACT_DIR / "model.joblib")
    preds = pd.read_csv(ARTIFACT_DIR / "test_predictions.csv")
    metrics = json.loads((ARTIFACT_DIR / "metrics.json").read_text())
    return model, preds, metrics


def _error_by_band(preds: pd.DataFrame) -> pd.DataFrame:
    df = preds.copy()
    df["ape"] = (df["actual_price"] - df["predicted_price"]).abs() / df["actual_price"]
    bands = pd.cut(
        df["actual_price"],
        bins=[0, 30_000, 60_000, 100_000, 200_000, np.inf],
        labels=["<30k", "30-60k", "60-100k", "100-200k", "200k+"],
    )
    return df.groupby(bands, observed=True).agg(
        n=("ape", "size"), mean_ape=("ape", "mean"), median_ape=("ape", "median")
    )


def _feature_importances(model) -> pd.Series:
    pipeline = model.regressor_  # fitted Pipeline inside TransformedTargetRegressor
    names = pipeline.named_steps["prep"].get_feature_names_out()
    importances = pipeline.named_steps["model"].feature_importances_
    return pd.Series(importances, index=names).sort_values(ascending=False)


def evaluate() -> None:
    model, preds, metrics = _load()

    print(f"Source: {metrics['source']}  |  test rows: {metrics['n_test']:,}")
    print(
        f"MAE {metrics['mae']:,.0f} SAR  |  R^2 {metrics['r2']:.3f}  |  "
        f"MAPE {metrics['mape']*100:.1f}%  |  median APE {metrics['median_ape']*100:.1f}%\n"
    )

    print("Error by price band:")
    band = _error_by_band(preds)
    for label, row in band.iterrows():
        print(
            f"  {label:>9}: n={int(row['n']):>5}  "
            f"mean APE {row['mean_ape']*100:>5.1f}%  median APE {row['median_ape']*100:>5.1f}%"
        )

    importances = _feature_importances(model)
    print("\nTop 12 features:")
    for name, val in importances.head(12).items():
        print(f"  {name:<28} {val:.3f}")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        top = importances.head(15)[::-1]
        plt.figure(figsize=(8, 6))
        plt.barh(top.index, top.values, color="#2563eb")
        plt.title("Valuation model — feature importance")
        plt.tight_layout()
        plt.savefig(ARTIFACT_DIR / "feature_importance.png", dpi=120)
        plt.close()

        plt.figure(figsize=(6, 6))
        plt.scatter(preds["actual_price"], preds["predicted_price"], s=6, alpha=0.3)
        lim = float(preds[["actual_price", "predicted_price"]].to_numpy().max())
        plt.plot([0, lim], [0, lim], "r--", linewidth=1)
        plt.xlabel("Actual price (SAR)")
        plt.ylabel("Predicted price (SAR)")
        plt.title("Actual vs predicted")
        plt.tight_layout()
        plt.savefig(ARTIFACT_DIR / "actual_vs_predicted.png", dpi=120)
        plt.close()
        print(f"\nPlots saved -> {ARTIFACT_DIR}")
    except ImportError:
        print("\n(matplotlib not installed — skipped plots)")


if __name__ == "__main__":
    evaluate()
