from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _ts_to_dt(value: int | float | None) -> datetime | None:
    if value in (None, 0):
        return None
    if value > 10_000_000_000:
        value = value / 1000
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _div_1000(value: int | float | None) -> float | None:
    if value in (None, 0):
        return 0.0 if value == 0 else None
    return round(float(value) / 1000, 3)


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
    def from_api(cls, data: dict[str, Any]) -> "CE04Data":
        bike_id = str(
            data.get("itemId")
            or data.get("vehicleId")
            or data.get("vin")
            or data.get("hashedShortVin")
            or data.get("typeKey")
            or "ce04"
        )

        battery_level = data.get("energyLevel") or data.get("fuelLevel")
        remaining_range_electric_raw = (
            data.get("remainingRangeElectric") or data.get("remainingRange")
        )

        return cls(
            bike_id=bike_id,
            name=data.get("name"),
            vin=data.get("vin"),
            type_key=data.get("typeKey"),
            color=data.get("color"),
            battery_level=battery_level,
            remaining_range_electric_km=_div_1000(remaining_range_electric_raw),
            charging_time_estimation_electric=data.get("chargingTimeEstimationElectric"),
            soc_max_electric=data.get("socMaxElectric"),
            total_mileage_km=_div_1000(data.get("totalMileage")),
            trip1_km=_div_1000(data.get("trip1")),
            trip2_km=_div_1000(data.get("trip2")),
            total_connected_distance_km=_div_1000(data.get("totalConnectedDistance")),
            next_service_remaining_distance_km=_div_1000(
                data.get("nextServiceRemainingDistance")
            ),
            tire_pressure_front_bar=data.get("tirePressureFront"),
            tire_pressure_rear_bar=data.get("tirePressureRear"),
            next_service_due_date=_ts_to_dt(data.get("nextServiceDueDate")),
            last_connected_time=_ts_to_dt(data.get("lastConnectedTime")),
            last_activated_time=_ts_to_dt(data.get("lastActivatedTime")),
            latitude=data.get("lastConnectedLat"),
            longitude=data.get("lastConnectedLon"),
            raw=data,
        )
