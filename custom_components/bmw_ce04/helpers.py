from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def parse_timestamp(value: Any) -> datetime | None:
    """Convert BMW timestamps (epoch ms/s or ISO string) to datetime."""
    if value in (None, 0, ""):
        return None

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    try:
        if value > 10_000_000_000:  # milliseconds
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


def rnd(value: Any, ndigits: int = 1) -> float | None:
    """Round a numeric value, returning None for missing/invalid input."""
    if value is None:
        return None
    try:
        return round(float(value), ndigits)
    except Exception:
        return None
