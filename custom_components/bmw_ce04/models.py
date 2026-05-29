from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .helpers import (
    parse_timestamp,
    km_from_meters,
    map_color,
)


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

        # BMW sometimes sends remainingRangeElectric=None but remainingRange=118000
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
            color=map_color(api_obj.color),

            battery_level=api_obj.battery_level,
            remaining_range_electric_km=km_from_meters(remaining_range_raw),

            charging_time_estimation_electric=api_obj.charging_time_estimation_electric,
            soc_max_electric=api_obj.soc_max_electric,

            total_mileage_km=km_from_meters(api_obj.total_mileage_km),
            trip1_km=km_from_meters(api_obj.trip1_km),
            trip2_km=km_from_meters(api_obj.trip2_km),

            total_connected_distance_km=km_from_meters(api_obj.total_connected_distance_km),

            next_service_remaining_distance_km=km_from_meters(
                api_obj.next_service_remaining_distance_km
            ),
            next_service_due_date=parse_timestamp(api_obj.next_service_due_date),

            tire_pressure_front_bar=api_obj.tire_pressure_front_bar,
            tire_pressure_rear_bar=api_obj.tire_pressure_rear_bar,

            last_connected_time=parse_timestamp(api_obj.last_connected_time),
            last_activated_time=parse_timestamp(api_obj.last_activated_time),

            latitude=api_obj.latitude,
            longitude=api_obj.longitude,

            raw=api_obj.raw,
        )
