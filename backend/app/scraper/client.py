"""Polite HTTP client for Haraj: respects robots.txt, rate-limits, and retries.

Used only by the live source. The default pipeline runs against fixtures, so nothing
here hits the network unless you explicitly choose the live source.
"""

from __future__ import annotations

import time
import urllib.robotparser as robotparser

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

BASE = "https://haraj.com.sa"
USER_AGENT = "lowballer-bot/0.1 (+https://example.com/lowballer; market research)"


class HarajClient:
    def __init__(self, min_delay: float = 2.0, user_agent: str = USER_AGENT, timeout: float = 25.0):
        self.min_delay = min_delay
        self.user_agent = user_agent
        self._last = 0.0
        self._client = httpx.Client(
            headers={"User-Agent": user_agent}, timeout=timeout, follow_redirects=True
        )
        self._robots: robotparser.RobotFileParser | None = robotparser.RobotFileParser()
        try:
            self._robots.parse(self._client.get(f"{BASE}/robots.txt").text.splitlines())
        except Exception:
            self._robots = None  # fail open but stay rate-limited

    def can_fetch(self, url: str) -> bool:
        return self._robots is None or self._robots.can_fetch(self.user_agent, url)

    def _throttle(self) -> None:
        wait = self.min_delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        retry=retry_if_exception_type(httpx.TransportError),
        reraise=True,
    )
    def get(self, url: str) -> str:
        if not self.can_fetch(url):
            raise PermissionError(f"robots.txt disallows fetching {url}")
        self._throttle()
        resp = self._client.get(url)
        resp.raise_for_status()
        return resp.text

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HarajClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
