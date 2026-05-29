from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .helpers import parse_timestamp, km_from_meters


@dataclass(slots=True)
class CE04Data:
    """Data model for the BMW CE 04 electric scooter."""

    bike_id: str
    name: str | None
    vin: str | None
    type_key: str | None
    color: str | None  # raw BMW color code e.g. "P0NB5"

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
    def from_api(cls, data: dict[str, Any]) -> "CE04Data":
        """Create CE04Data from a raw BMW API dict."""

        # remainingRangeElectric is null in API, fallback to remainingRange
        remaining_range_raw = (
            data.get("remainingRangeElectric")
            if data.get("remainingRangeElectric") is not None
            else data.get("remainingRange")
        )

        # lastActivatedTime = 0 means never activated
        last_activated_raw = data.get("lastActivatedTime")
        if last_activated_raw == 0:
            last_activated_raw = None

        return cls(
            bike_id=data.get("itemId") or data.get("vehicleId") or "",
            name=data.get("name"),
            vin=data.get("vin"),
            type_key=data.get("typeKey"),
            color=data.get("color"),  # raw code, e.g. "P0NB5"

            battery_level=data.get("energyLevel"),
            remaining_range_electric_km=km_from_meters(remaining_range_raw),

            charging_time_estimation_electric=data.get("chargingTimeEstimationElectric"),
            soc_max_electric=data.get("socMax"),

            total_mileage_km=km_from_meters(data.get("totalMileage")),
            trip1_km=km_from_meters(data.get("trip1")),
            trip2_km=km_from_meters(data.get("trip2")),
            total_connected_distance_km=km_from_meters(data.get("totalConnectedDistance")),

            next_service_remaining_distance_km=km_from_meters(
                data.get("nextServiceRemainingDistance")
            ),
            next_service_due_date=parse_timestamp(data.get("nextServiceDueDate")),

            tire_pressure_front_bar=data.get("tirePressureFront"),
            tire_pressure_rear_bar=data.get("tirePressureRear"),

            last_connected_time=parse_timestamp(data.get("lastConnectedTime")),
            last_activated_time=parse_timestamp(last_activated_raw),

            latitude=data.get("lastConnectedLat"),
            longitude=data.get("lastConnectedLon"),

            raw=data,
        )
