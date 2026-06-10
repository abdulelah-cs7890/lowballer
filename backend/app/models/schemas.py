"""Pydantic response schemas for the API (eBay products)."""

from __future__ import annotations

from pydantic import BaseModel


class DealOut(BaseModel):
    id: str
    make: str | None        # category (GPU, Phone, …)
    model: str | None       # product model (RTX 4090, …)
    url: str | None
    title: str | None
    image: str | None = None
    condition: str | None = None
    asking_price: float
    predicted_price: float  # fair value = comps median
    percent_below: float
    needs_review: bool


class CompOut(BaseModel):
    make: str | None
    model: str | None
    title: str | None = None
    condition: str | None = None
    asking_price: float


class DealDetailOut(DealOut):
    comps: list[CompOut]


class HealthOut(BaseModel):
    status: str
    open_deals: int
