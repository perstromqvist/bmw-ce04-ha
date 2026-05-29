from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def parse_timestamp(value: Any) -> datetime | None:
    """Convert BMW timestamps (epoch or ISO) to datetime."""
    if value in (None, 0, ""):
        return None

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    try:
        if value > 10_000_000_000:  # ms
            value = value / 1000
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except Exception:
        return None


def km_from_meters(value: Any) -> float | None:
    """Convert BMW meter values to km."""
    if value is None:
        return None
    try:
        return round(float(value) / 1000, 3)
    except Exception:
        return None


COLOR_MAP = {
    "P0N3H": "white",
    "P0NB5": "blue",
    "P0N2M": "silver",
}

def map_color(code: str | None) -> str:
    if not code:
        return "unknown"
    return COLOR_MAP.get(code, "unknown")
