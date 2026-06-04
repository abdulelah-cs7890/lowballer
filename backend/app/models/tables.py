"""SQLAlchemy ORM models: listings, valuations, flags.

These mirror `supabase/schema.sql` so the same shape works on SQLite (dev) and
Supabase Postgres (prod).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Listing(Base):
    """A car listing (scraped from Haraj, or seeded), normalized to the model schema."""

    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. haraj listing id
    source: Mapped[str] = mapped_column(String, default="seed")
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)

    make: Mapped[str | None] = mapped_column(String, nullable=True)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mileage_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engine_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String, nullable=True)
    gear_type: Mapped[str | None] = mapped_column(String, nullable=True)
    origin: Mapped[str | None] = mapped_column(String, nullable=True)
    region: Mapped[str | None] = mapped_column(String, nullable=True)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    options: Mapped[str | None] = mapped_column(String, nullable=True)

    asking_price: Mapped[float] = mapped_column(Float, nullable=False)
    scraped_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())


class Valuation(Base):
    """A model's fair-value estimate for a listing at a point in time."""

    __tablename__ = "valuations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id"), index=True)
    predicted_price: Mapped[float] = mapped_column(Float)
    percent_below: Mapped[float] = mapped_column(Float)  # (pred - asking) / pred
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    model_mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())


class Flag(Base):
    """A surfaced deal: a listing whose valuation crossed the flag threshold."""

    __tablename__ = "flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[str] = mapped_column(ForeignKey("listings.id"), index=True)
    valuation_id: Mapped[int] = mapped_column(ForeignKey("valuations.id"))
    percent_below: Mapped[float] = mapped_column(Float)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String, default="open")  # open | dismissed
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
