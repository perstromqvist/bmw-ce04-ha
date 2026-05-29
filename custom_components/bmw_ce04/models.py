from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


def _parse_timestamp(value: Any) -> Optional[datetime]:
    """Convert API timestamp (epoch or ISO string) to datetime."""
    if value in (None, 0, ""):
        return None

    # ISO string
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    # Epoch (ms or s)
    try:
        if value > 10_000_000_000:  # ms
            value = value / 1000
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except Exception:
        return None


def _div_1000(value: Any) -> Optional[float]:
    """Convert BMW integer millimeters/meters to km."""
    if value is None:
        return None
    try:
        return round(float(value) / 1000, 3)
    except Exception:
        return None


@dataclass(slots=True)
class CE04Data:
    """Data model for the BMW CE 04 electric scooter."""

    bike_id: str
    name: str | None
    vin: str | None
    type_key: str | None
    color: str | None

    battery_level: int | float | None
    remaining_range_electric_km: float | None
    charging_time_estimation_electric: int | None
    soc_max_electric: int | float | None

    total_mileage_km: float | None
    trip1_km: float | None
    trip2_km: float | None
    total_connected_distance_km: float | None

    next_service_remaining_distance_km: float | None
    next_service_due_date: datetime | None

    tire_pressure_front_bar: float | None
    tire_pressure_rear_bar: float | None

    last_connected_time: datetime | None
    last_activated_time: datetime | None

    latitude: float | None
    longitude: float | None

    raw: dict[str, Any]

    @classmethod
    def from_api(cls, api_obj: Any) -> "CE04Data":
        """Create CE04Data from API dataclass."""

        # Range: BMW sometimes sends remainingRangeElectric=None but remainingRange=118000
        remaining_range_raw = (
            api_obj.remaining_range_electric_km
            if api_obj.remaining_range_electric_km is not None
            else api_obj.raw.get("remainingRange")
        )

        return cls(
            bike_id=api_obj.bike_id,
            name=api_obj.name,
            vin=api_obj.vin,
            type_key=api_obj.type_key,
            color=api_obj.color,

            battery_level=api_obj.battery_level,
            remaining_range_electric_km=_div_1000(remaining_range_raw),

            charging_time_estimation_electric=api_obj.charging_time_estimation_electric,
            soc_max_electric=api_obj.soc_max_electric,

            total_mileage_km=_div_1000(api_obj.total_mileage_km),
            trip1_km=_div_1000(api_obj.trip1_km),
            trip2_km=_div_1000(api_obj.trip2_km),

            total_connected_distance_km=_div_1000(api_obj.total_connected_distance_km),

            next_service_remaining_distance_km=_div_1000(
                api_obj.next_service_remaining_distance_km
            ),
            next_service_due_date=_parse_timestamp(api_obj.next_service_due_date),

            tire_pressure_front_bar=api_obj.tire_pressure_front_bar,
            tire_pressure_rear_bar=api_obj.tire_pressure_rear_bar,

            last_connected_time=_parse_timestamp(api_obj.last_connected_time),
            last_activated_time=_parse_timestamp(api_obj.last_activated_time),

            latitude=api_obj.latitude,
            longitude=api_obj.longitude,

            raw=api_obj.raw,
        )
