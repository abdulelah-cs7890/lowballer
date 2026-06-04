"""Pydantic response schemas for the API."""

from __future__ import annotations

from pydantic import BaseModel


class DealOut(BaseModel):
    id: str
    make: str | None
    model: str | None
    year: int | None
    mileage_km: int | None
    region: str | None
    url: str | None
    title: str | None
    asking_price: float
    predicted_price: float
    percent_below: float
    needs_review: bool
    model_mae: float | None


class CompOut(BaseModel):
    make: str | None
    model: str | None
    year: int | None
    mileage_km: int | None
    asking_price: float


class DealDetailOut(DealOut):
    engine_size: float | None
    fuel_type: str | None
    gear_type: str | None
    origin: str | None
    color: str | None
    options: str | None
    comps: list[CompOut]


class HealthOut(BaseModel):
    status: str
    model_loaded: bool
    open_deals: int
