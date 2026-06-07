"""Extract structured fields from a Haraj listing's React-Router data stream.

Haraj client-side-renders listing details, so the price / mileage / category live only
in the turbo-stream payload inside `streamController.enqueue("...")` — never in the
visible HTML. That payload is a flattened, de-duplicated *pool* array; an object's field
is stored as `{"_<keyIndex>": valueRef}` where both are indices into the pool. We parse
the pool and resolve the few fields we need (the make/model/year still come from the clean
`og:title` via the normalizer; this is mainly how we recover the **price**).
"""

from __future__ import annotations

import json

_TOKEN = 'enqueue("'


def _enqueue_strings(html: str) -> list[str]:
    """Return each `enqueue("…")` argument as a JSON string literal (escapes intact)."""
    out: list[str] = []
    i = 0
    while True:
        k = html.find(_TOKEN, i)
        if k < 0:
            break
        j = k + len(_TOKEN)
        buf: list[str] = []
        while j < len(html):
            ch = html[j]
            if ch == "\\":  # keep escape pairs together
                buf.append(html[j : j + 2])
                j += 2
                continue
            if ch == '"':  # unescaped quote ends the JS string
                break
            buf.append(ch)
            j += 1
        out.append('"' + "".join(buf) + '"')
        i = j + 1
    return out


def parse_pool(html: str) -> list:
    """Decode the turbo-stream into its flat pool array (largest enqueue chunk)."""
    best: list = []
    for lit in _enqueue_strings(html):
        try:
            pool = json.loads(json.loads(lit))  # unescape JS string, then parse array
        except Exception:
            continue
        if isinstance(pool, list) and len(pool) > len(best):
            best = pool
    return best


def field(pool: list, name: str):
    """Resolve a field value by name via the pool's `{"_<keyIdx>": valueRef}` encoding."""
    try:
        ni = pool.index(name)
    except ValueError:
        return None
    key = f"_{ni}"
    for v in pool:
        if isinstance(v, dict) and key in v:
            ref = v[key]
            if isinstance(ref, int) and 0 <= ref < len(pool):
                return pool[ref]
            return ref
    return None


def extract_stream_fields(html: str) -> dict:
    """Pull the structured fields we care about from a listing page (best-effort)."""
    pool = parse_pool(html)
    if not pool:
        return {}

    def num(x):
        return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None

    return {
        "is_car": field(pool, "carOrRelated") == "CAR",
        "price": num(field(pool, "price")),
        "year": num(field(pool, "model")),  # Haraj's carInfo.model is the model *year*
        "mileage_km": num(field(pool, "mileage")),
        "fuel": field(pool, "fuel"),
        "gear": field(pool, "gear"),
    }
