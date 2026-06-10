"""Valuation: shared feature schema, model inference, and flag logic.

This package is the single source of truth for how a car (whether a row from the
training dataset or a freshly-scraped Haraj listing) is turned into model features
and a fair-value prediction. Both `legacy/ml/train.py` and `legacy/worker.py` import from
here so training and serving can never drift apart.
"""
