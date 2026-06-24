from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .helpers import parse_timestamp, km_from_meters, rnd


@dataclass(slots=True)
class CE04Data:
    """Data model for the BMW CE 04 electric scooter."""

    bike_id: str
    name: str | None
    vin: str | None
    type_key: str | None
    color: str | None  # raw BMW color code e.g. "P0NB5"

    vehicle_id: str | None  # hashed id used to link recorded tracks

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
            vehicle_id=data.get("vehicleId"),
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


@dataclass(slots=True)
class RecordedTrack:
    """A single recorded ride from BMW CloudSync."""

    track_id: str | None
    title: str | None
    bike_id: str | None  # matches CE04Data.vehicle_id

    start_time: datetime | None
    end_time: datetime | None
    start_lat: float | None
    start_lon: float | None
    end_lat: float | None
    end_lon: float | None

    distance_km: float | None
    ride_time_s: int | None
    speed_avg_kmh: float | None
    speed_max_kmh: float | None

    temp_max_c: float | None
    temp_min_c: float | None
    elevation_max_m: float | None
    elevation_min_m: float | None
    engine_max_rpm: int | None
    lean_left_max: float | None
    lean_right_max: float | None
    acceleration_max: float | None
    deceleration_max: float | None

    raw: dict[str, Any]

    @classmethod
    def from_api(cls, d: dict[str, Any]) -> "RecordedTrack":
        """Create a RecordedTrack from a raw CloudSync dict (null-safe)."""
        return cls(
            track_id=d.get("itemId"),
            title=d.get("title"),
            bike_id=d.get("bikeId"),
            start_time=parse_timestamp(d.get("startTimestamp")),
            end_time=parse_timestamp(d.get("endTimestamp")),
            start_lat=d.get("startLat"),
            start_lon=d.get("startLon"),
            end_lat=d.get("endLat"),
            end_lon=d.get("endLon"),
            distance_km=km_from_meters(d.get("rideDistance")),
            ride_time_s=d.get("rideTime"),
            speed_avg_kmh=rnd(d.get("speedAverageKmh")),
            speed_max_kmh=rnd(d.get("speedMaxKmh")),
            temp_max_c=rnd(d.get("temperatureMaxC")),
            temp_min_c=rnd(d.get("temperatureMinC")),
            elevation_max_m=rnd(d.get("elevationMaxM")),
            elevation_min_m=rnd(d.get("elevationMinM")),
            engine_max_rpm=d.get("engineMaxRpm"),
            lean_left_max=rnd(d.get("leanAngleLeftMax")),
            lean_right_max=rnd(d.get("leanAngleRightMax")),
            acceleration_max=rnd(d.get("accelerationMax"), 2),
            deceleration_max=rnd(d.get("decelerationMax"), 2),
            raw=d,
        )
