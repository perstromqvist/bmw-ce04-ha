from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .const import COLOR_MAP, DEFAULT_COLOR   # ← lägg till denna import


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


def map_color(code: str | None) -> str:
    """Map BMW color code to filename."""
    if not code:
        return DEFAULT_COLOR
    return COLOR_MAP.get(code, DEFAULT_COLOR)   # ← ändra "unknown" till DEFAULT_COLOR
