"""Periodic eBay refresh — keeps deals current and feeds the realtime SSE stream, so newly
underpriced listings appear on the dashboard (toast + bell) without a manual re-ingest.

    python -m app.ebay.scheduler            # loop forever (default 15 min)
    python -m app.ebay.scheduler --once     # single refresh (testing / demos)
    python -m app.ebay.scheduler --interval 600

Also embeddable in the API process via REFRESH_INTERVAL_SECONDS (see app.main lifespan).
"""

from __future__ import annotations

import argparse
import asyncio

from app.db import init_db
from app.ebay.ingest import refresh


async def run_loop(interval: int) -> None:
    init_db()
    while True:
        await asyncio.to_thread(refresh)  # eBay I/O off the event loop
        await asyncio.sleep(interval)


def main() -> None:
    ap = argparse.ArgumentParser(description="Lowballer eBay deal refresher")
    ap.add_argument("--once", action="store_true", help="run a single refresh and exit")
    ap.add_argument("--interval", type=int, default=900, help="seconds between refreshes")
    args = ap.parse_args()
    if args.once:
        refresh()
    else:
        asyncio.run(run_loop(args.interval))


if __name__ == "__main__":
    main()
