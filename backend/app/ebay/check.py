"""Quick connectivity check for the eBay Browse API.

    python -m app.ebay.check "RTX 4090"
"""

from __future__ import annotations

import statistics
import sys

from app.ebay.client import EbayClient


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "RTX 4090"
    with EbayClient() as ebay:
        items = ebay.search(query, limit=50)
    print(f'"{query}": {len(items)} used listings')
    if not items:
        return
    prices = sorted(i["price"] for i in items)
    median = statistics.median(prices)
    print(f"  price range {prices[0]:.0f}–{prices[-1]:.0f} {items[0]['currency']}, median {median:.0f}")
    print("  cheapest 3:")
    for it in sorted(items, key=lambda x: x["price"])[:3]:
        below = (median - it["price"]) / median * 100
        print(f"    {it['price']:>8.0f}  ({below:+.0f}% vs median)  {it['title'][:60]}")


if __name__ == "__main__":
    main()
