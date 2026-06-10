"""SQLAlchemy ORM models: listings, valuations, flags.

These ORM models are the schema's single source of truth (created at startup via
`init_db()`); the same shape works on SQLite (dev) and Supabase Postgres (prod).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Listing(Base):
    """A product listing (eBay), de-duplicated by its listing id."""

    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # eBay item id
    source: Mapped[str] = mapped_column(String, default="ebay")
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)

    make: Mapped[str | None] = mapped_column(String, nullable=True)   # category (GPU, Phone, …)
    model: Mapped[str | None] = mapped_column(String, nullable=True)  # product model (RTX 4090, …)
    image: Mapped[str | None] = mapped_column(String, nullable=True)
    condition: Mapped[str | None] = mapped_column(String, nullable=True)

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
