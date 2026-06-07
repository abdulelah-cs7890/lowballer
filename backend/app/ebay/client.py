"""Minimal eBay Browse API client (application/client-credentials OAuth).

Docs: https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
Set EBAY_CLIENT_ID / EBAY_CLIENT_SECRET in backend/.env (production keyset).
"""

from __future__ import annotations

import base64
import time

import httpx

from app.config import settings

OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
SCOPE = "https://api.ebay.com/oauth/api_scope"


class EbayError(RuntimeError):
    pass


class EbayClient:
    def __init__(self, client_id: str | None = None, client_secret: str | None = None, marketplace: str | None = None):
        self.client_id = client_id or settings.ebay_client_id
        self.client_secret = client_secret or settings.ebay_client_secret
        self.marketplace = marketplace or settings.ebay_marketplace
        if not (self.client_id and self.client_secret):
            raise EbayError("Missing eBay credentials (set EBAY_CLIENT_ID / EBAY_CLIENT_SECRET).")
        self._http = httpx.Client(timeout=30)
        self._token: str | None = None
        self._token_exp = 0.0

    def _basic_auth(self) -> str:
        raw = f"{self.client_id}:{self.client_secret}".encode()
        return "Basic " + base64.b64encode(raw).decode()

    def token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        r = self._http.post(
            OAUTH_URL,
            headers={"Authorization": self._basic_auth(), "Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "scope": SCOPE},
        )
        if r.status_code != 200:
            raise EbayError(f"OAuth failed ({r.status_code}): {r.text[:200]}")
        d = r.json()
        self._token = d["access_token"]
        self._token_exp = time.time() + int(d.get("expires_in", 7200))
        return self._token

    def search(
        self,
        query: str,
        *,
        limit: int = 50,
        condition_ids: str | None = "3000",
        category_ids: str | None = None,
    ) -> list[dict]:
        """Search active listings for `query`; return normalized item dicts.

        `condition_ids` is an eBay condition id set (3000 = Used) — excludes New and
        "For parts". `category_ids` restricts to a category (e.g. 27386 = Graphics Cards).
        """
        params: dict[str, str] = {"q": query, "limit": str(min(limit, 200))}
        if condition_ids:
            params["filter"] = f"conditionIds:{{{condition_ids}}}"
        if category_ids:
            params["category_ids"] = category_ids
        r = self._http.get(
            BROWSE_URL,
            headers={"Authorization": f"Bearer {self.token()}", "X-EBAY-C-MARKETPLACE-ID": self.marketplace},
            params=params,
        )
        if r.status_code != 200:
            raise EbayError(f"Browse search failed ({r.status_code}): {r.text[:200]}")

        out: list[dict] = []
        for it in r.json().get("itemSummaries") or []:
            price = it.get("price") or {}
            try:
                value = float(price.get("value"))
            except (TypeError, ValueError):
                continue
            out.append(
                {
                    "id": it.get("itemId"),
                    "title": it.get("title"),
                    "price": value,
                    "currency": price.get("currency"),
                    "condition": it.get("condition"),
                    "url": it.get("itemWebUrl"),
                    "image": (it.get("image") or {}).get("imageUrl"),
                    "model": query,  # the search term groups comps
                }
            )
        return out

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "EbayClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
