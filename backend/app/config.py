"""Runtime configuration. Values come from env vars / a local `.env` file.

The whole point of `database_url`: it's `sqlite` for local dev and a Supabase Postgres
connection string in production — the rest of the code never changes.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # SQLite for local dev; set to a Supabase Postgres URL in prod, e.g.
    #   postgresql+psycopg2://postgres:<pw>@db.<ref>.supabase.co:5432/postgres
    database_url: str = "sqlite:///./lowballer.db"

    # A listing must be this far below predicted value to be flagged as a deal.
    flag_threshold: float = 0.12

    # Comma-separated origins allowed to call the API (the Next.js dev server).
    cors_origins: str = "http://localhost:3000"

    # eBay Browse API (client-credentials OAuth). Get keys at developer.ebay.com.
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_marketplace: str = "EBAY_US"

    # Auto-refresh inside the API process (seconds). 0 = off (run the scheduler standalone).
    refresh_interval_seconds: int = 0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
