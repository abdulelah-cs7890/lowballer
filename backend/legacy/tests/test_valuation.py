"""Tests for the valuation feature schema and flag logic."""

from __future__ import annotations

import pandas as pd
import pytest

from legacy.valuation.features import (
    FEATURE_COLUMNS,
    REFERENCE_YEAR,
    add_derived_features,
    prepare_features,
)
from legacy.valuation.model import MODEL_PATH, Valuator

CAR = dict(
    make="Toyota", model="Camry", year=2019, mileage_km=90_000, engine_size=2.5,
    fuel_type="Gas", gear_type="Automatic", origin="Saudi", region="Riyadh",
    color="White", options="Full", price=55_000,
)


def test_prepare_features_returns_exact_model_columns():
    X = prepare_features(pd.DataFrame([CAR]))
    assert list(X.columns) == FEATURE_COLUMNS


def test_derived_features():
    out = add_derived_features(pd.DataFrame([CAR]))
    assert out["age"].iloc[0] == REFERENCE_YEAR - 2019
    assert out["log_mileage"].iloc[0] > 0


def test_missing_categorical_is_imputed():
    car = {k: v for k, v in CAR.items() if k != "color"}
    out = add_derived_features(pd.DataFrame([car]))
    assert out["color"].iloc[0] == "unknown"


needs_model = pytest.mark.skipif(
    not MODEL_PATH.exists(), reason="model artifact missing; run `python -m legacy.ml.train`"
)


@needs_model
def test_predicted_value_is_plausible():
    v = Valuator()
    pred = v.predict([CAR])[0]
    assert 20_000 < pred < 150_000  # a used Camry lives in this range


@needs_model
def test_flag_thresholds():
    v = Valuator()
    fair = v.predict([CAR])[0]
    assert v.value({**CAR, "price": round(fair)}).is_flagged is False
    deal = v.value({**CAR, "price": round(fair * 0.8)})
    assert deal.is_flagged and not deal.needs_review
    scam = v.value({**CAR, "price": round(fair * 0.4)})
    assert scam.is_flagged and scam.needs_review
