"""Backtest the mispricing *detector* (not just the model).

A good valuation model isn't enough — what matters is whether the flag rule
("asking is >= threshold below predicted") actually catches genuinely underpriced
cars without crying wolf. We can't replay historical Haraj delistings, so we simulate
listings against the held-out test set, whose `actual_price` we treat as true market
value:

  - asking = actual_price * (1 - d),  d ~ U(-10%, +40%)   (some over-, some under-priced)
  - ground truth "deal"  := asking <= 85% of true market value (>= 15% genuinely below)
  - detector flags       := (predicted - asking) / predicted >= threshold

Because the detector only sees the *model's* estimate, its precision/recall reflect
real model error. Run after training:

    python -m ml.backtest
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ART = Path(__file__).resolve().parent / "artifacts"
TRUE_DISCOUNT = 0.15  # a "real" deal is >= 15% below true market value
THRESHOLDS = [0.08, 0.10, 0.12, 0.15, 0.20, 0.25]


def _prf(pred_flag: np.ndarray, y_true: np.ndarray) -> tuple[float, float, float]:
    tp = int((pred_flag & y_true).sum())
    fp = int((pred_flag & ~y_true).sum())
    fn = int((~pred_flag & y_true).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def backtest(seed: int = 0) -> dict:
    df = pd.read_csv(ART / "test_predictions.csv")
    actual = df["actual_price"].to_numpy(dtype=float)
    predicted = df["predicted_price"].to_numpy(dtype=float)

    rng = np.random.default_rng(seed)
    d = rng.uniform(-0.10, 0.40, len(df))
    asking = actual * (1 - d)
    y_true = asking <= actual * (1 - TRUE_DISCOUNT)
    pct_below = (predicted - asking) / predicted

    table = []
    for thr in THRESHOLDS:
        precision, recall, f1 = _prf(pct_below >= thr, y_true)
        table.append(
            {"threshold": thr, "flagged": int((pct_below >= thr).sum()),
             "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}
        )

    best = max(table, key=lambda r: r["f1"])
    result = {
        "n_test": int(len(df)),
        "true_positive_rate": round(float(y_true.mean()), 3),
        "by_threshold": table,
        "best_f1_threshold": best["threshold"],
    }
    ART.mkdir(parents=True, exist_ok=True)
    (ART / "backtest.json").write_text(json.dumps(result, indent=2))

    print(f"Backtest on {len(df):,} held-out cars  ({y_true.mean()*100:.0f}% are real deals)\n")
    print(f"  {'thr':>5} {'flagged':>8} {'precision':>10} {'recall':>8} {'f1':>6}")
    for r in table:
        mark = "  <- best F1" if r["threshold"] == best["threshold"] else ""
        print(f"  {r['threshold']:>5.2f} {r['flagged']:>8} {r['precision']:>10.2f} "
              f"{r['recall']:>8.2f} {r['f1']:>6.2f}{mark}")

    _plot(actual, predicted, asking, y_true, pct_below)
    return result


def _plot(actual, predicted, asking, y_true, pct_below) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return

    ts = np.linspace(0.0, 0.4, 60)
    precisions, recalls = [], []
    for t in ts:
        p, r, _ = _prf(pct_below >= t, y_true)
        precisions.append(p)
        recalls.append(r)
    plt.figure(figsize=(6, 5))
    plt.plot(recalls, precisions, color="#2563eb")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Mispricing detector — precision vs recall")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(ART / "pr_curve.png", dpi=120)
    plt.close()
    print(f"\nPR curve saved -> {ART / 'pr_curve.png'}")


if __name__ == "__main__":
    backtest()
