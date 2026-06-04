"""Synthetic Saudi used-car dataset generator.

Lets the whole pipeline run end-to-end *today*, with zero downloads, while producing
data whose schema is identical to the real Kaggle "Saudi Arabia Used Cars" set. Prices
follow a plausible depreciation/mileage/engine model plus noise, so the trained model
has a real (learnable) signal and reports meaningful MAE/R2.

Drop the real CSV at `ml/data/saudi_used_cars.csv` and the loader uses that instead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# make -> (base value in SAR for a recent model, list of model/trim names)
_MAKES = {
    "Toyota": (110_000, ["Camry", "Corolla", "Land Cruiser", "Hilux", "Yaris"]),
    "Hyundai": (85_000, ["Sonata", "Elantra", "Accent", "Tucson", "Azera"]),
    "Ford": (95_000, ["Taurus", "Explorer", "F-150", "Edge", "Expedition"]),
    "Nissan": (90_000, ["Altima", "Patrol", "Sunny", "Xterra", "Maxima"]),
    "Lexus": (180_000, ["ES", "LX", "GX", "IS", "RX"]),
    "Chevrolet": (88_000, ["Tahoe", "Impala", "Silverado", "Malibu", "Suburban"]),
    "Kia": (80_000, ["Optima", "Cerato", "Sportage", "Sorento", "Rio"]),
    "GMC": (150_000, ["Yukon", "Sierra", "Acadia", "Terrain"]),
    "Honda": (92_000, ["Accord", "Civic", "CR-V", "Pilot"]),
    "Mercedes": (220_000, ["C-Class", "E-Class", "S-Class", "GLE"]),
}
_ORIGINS = ["Saudi", "Gulf Arabic", "Imported", "Other"]
_REGIONS = ["Riyadh", "Jeddah", "Dammam", "Makkah", "Madinah", "Abha", "Tabuk"]
_COLORS = ["White", "Black", "Silver", "Gray", "Blue", "Red", "Brown"]
_FUEL = ["Gas", "Diesel", "Hybrid"]
_GEAR = ["Automatic", "Manual"]
_OPTIONS = ["Full", "Semi Full", "Standard"]
_OPTIONS_MULT = {"Full": 1.12, "Semi Full": 1.04, "Standard": 0.94}
_ORIGIN_MULT = {"Saudi": 1.0, "Gulf Arabic": 0.97, "Imported": 0.9, "Other": 0.85}


def make_synthetic_dataset(n: int = 9000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    makes = list(_MAKES)
    rows = []
    for _ in range(n):
        make = rng.choice(makes)
        base, models = _MAKES[make]
        model = rng.choice(models)
        year = int(rng.integers(2003, 2025))
        age = 2025 - year
        mileage = int(max(0, rng.normal(age * 18_000, 30_000)))
        engine = round(float(rng.choice([1.5, 1.6, 2.0, 2.4, 2.5, 3.0, 3.5, 4.0, 5.7])), 1)
        fuel = rng.choice(_FUEL, p=[0.86, 0.08, 0.06])
        gear = rng.choice(_GEAR, p=[0.9, 0.1])
        origin = rng.choice(_ORIGINS, p=[0.55, 0.25, 0.15, 0.05])
        region = rng.choice(_REGIONS)
        color = rng.choice(_COLORS)
        options = rng.choice(_OPTIONS, p=[0.4, 0.35, 0.25])

        # plausible price model
        depreciation = 0.90 ** age
        mileage_factor = max(0.45, 1.0 - mileage / 600_000)
        engine_factor = 0.9 + 0.05 * engine
        value = (
            base
            * depreciation
            * mileage_factor
            * engine_factor
            * _OPTIONS_MULT[options]
            * _ORIGIN_MULT[origin]
        )
        value *= rng.normal(1.0, 0.08)  # idiosyncratic noise (the part we can't predict)
        price = int(max(8_000, round(value, -2)))

        rows.append(
            {
                "make": make,
                "model": model,
                "year": year,
                "mileage_km": mileage,
                "engine_size": engine,
                "fuel_type": fuel,
                "gear_type": gear,
                "origin": origin,
                "region": region,
                "color": color,
                "options": options,
                "price": price,
            }
        )
    return pd.DataFrame(rows)
