from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATIC_PATH
from .entity import CE04Entity
from .helpers import rnd
from .models import CE04Data, RecordedTrack

# Generic fallback image. Any colour code we don't ship an image for falls
# back to this — just drop your own www/mc_image.jpg in to customise it.
DEFAULT_IMAGE = "mc_image"

# Colour codes (lowercased) we ship a matching <code>.jpg for in www/.
# Decal variants carry a suffix (e.g. "p0nb5-ei00257p"); entity_picture tries
# the full code first, then the base colour before the dash. Add a code here
# when you add its image file.
AVAILABLE_IMAGES = {"p0nb5", "p0n2t", "p0n3l", "p0nb5-ei00257p"}


@dataclass(frozen=True, kw_only=True)
class CE04SensorDescription(SensorEntityDescription):
    value_fn: Callable[[CE04Data], object]


SENSORS: tuple[CE04SensorDescription, ...] = (
    CE04SensorDescription(
        key="battery_level",
        translation_key="battery_level",
        name="Battery level",
        icon="mdi:battery-charging",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.battery_level,
    ),
    CE04SensorDescription(
        key="remaining_range",
        translation_key="remaining_range",
        name="Remaining range",
        icon="mdi:map-marker-distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.remaining_range_electric_km,
    ),
    CE04SensorDescription(
        key="total_mileage",
        translation_key="total_mileage",
        name="Total mileage",
        icon="mdi:speedometer",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.total_mileage_km,
    ),
    CE04SensorDescription(
        key="trip1",
        translation_key="trip1",
        name="Trip 1",
        icon="mdi:road-variant",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.trip1_km,
    ),
    CE04SensorDescription(
        key="trip2",
        translation_key="trip2",
        name="Trip 2",
        icon="mdi:road-variant",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda bike: bike.trip2_km,
    ),
    CE04SensorDescription(
        key="tire_pressure_front",
        translation_key="tire_pressure_front",
        name="Tire pressure front",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda bike: bike.tire_pressure_front_bar,
    ),
    CE04SensorDescription(
        key="tire_pressure_rear",
        translation_key="tire_pressure_rear",
        name="Tire pressure rear",
        icon="mdi:gauge",
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda bike: bike.tire_pressure_rear_bar,
    ),
    CE04SensorDescription(
        key="vin",
        translation_key="vin",
        name="VIN",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda bike: bike.vin,
    ),
    CE04SensorDescription(
        key="next_service_due_date",
        translation_key="next_service_due_date",
        name="Next service due date",
        icon="mdi:wrench-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda bike: bike.next_service_due_date,
    ),
    CE04SensorDescription(
        key="next_service_remaining_distance",
        translation_key="next_service_remaining_distance",
        name="Next service remaining distance",
        icon="mdi:wrench-outline",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.next_service_remaining_distance_km,
    ),
    CE04SensorDescription(
        key="last_connected_time",
        translation_key="last_connected_time",
        name="Last connected time",
        icon="mdi:clock-check-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda bike: bike.last_connected_time,
    ),
    CE04SensorDescription(
        key="last_activated_time",
        translation_key="last_activated_time",
        name="Last activated time",
        icon="mdi:clock-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda bike: bike.last_activated_time,
    ),
    CE04SensorDescription(
        key="charging_time_estimation",
        translation_key="charging_time_estimation",
        name="Charging time estimation",
        icon="mdi:battery-clock",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda bike: bike.charging_time_estimation_electric,
    ),
    CE04SensorDescription(
        key="battery_soh",
        translation_key="battery_soh",
        name="Battery maximum capacity",
        icon="mdi:battery-heart-variant",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda bike: bike.soc_max_electric,
    ),
)


class CE04Sensor(CE04Entity, SensorEntity):
    """A standard BMW CE 04 sensor."""

    entity_description: CE04SensorDescription

    def __init__(self, coordinator, bike_id: str, description: CE04SensorDescription) -> None:
        super().__init__(coordinator, bike_id)
        self.entity_description = description
        self._attr_unique_id = f"{self.bike_slug}_{description.key}"
        self._attr_suggested_object_id = f"{self.bike_slug}_{description.key}"

    @property
    def native_value(self):
        if not self.bike:
            return None
        return self.entity_description.value_fn(self.bike)


class CE04VehicleImageSensor(CE04Entity, SensorEntity):
    """Sensor that exposes the CE 04 vehicle image via entity_picture."""

    _attr_has_entity_name = True
    _attr_translation_key = "vehicle_image"
    _attr_icon = "mdi:motorbike"

    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator, bike_id)
        self._attr_unique_id = f"{self.bike_slug}_vehicle_image"
        self._attr_suggested_object_id = "vehicle_image"

    @property
    def native_value(self) -> str:
        """State is the color code, e.g. P0NB5."""
        return (self.bike.color if self.bike else None) or DEFAULT_IMAGE

    @property
    def entity_picture(self) -> str:
        """URL to the vehicle image for the bike's colour.

        Tries the full colour code first (e.g. a decal variant like
        "p0nb5-ei00257p"), then the base colour before the dash, and finally
        mc_image.jpg for anything unknown.
        """
        code = ((self.bike.color if self.bike else None) or "").lower()
        base = code.split("-", 1)[0]
        if code in AVAILABLE_IMAGES:
            filename = code
        elif base in AVAILABLE_IMAGES:
            filename = base
        else:
            filename = DEFAULT_IMAGE
        return f"{STATIC_PATH}/{filename}.jpg"


class CE04LastUpdateSensor(CE04Entity, SensorEntity):
    """Timestamp of the integration's last successful poll.

    Stays available (showing the last success time) even when a poll fails, so it
    goes stale if the integration hangs — handy to alert on.
    """

    _attr_name = "Last update"
    _attr_icon = "mdi:clock-check-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator, bike_id)
        self._attr_unique_id = f"{self.bike_slug}_last_update"
        self._attr_suggested_object_id = f"{self.bike_slug}_last_update"

    @property
    def available(self) -> bool:
        # Unlike other entities, stay available when a poll fails so the (now
        # stale) timestamp can still be read and alerted on.
        return self.bike is not None

    @property
    def native_value(self):
        return self.coordinator.last_update_time


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMW CE 04 sensor entities."""
    coordinator = entry.runtime_data.coordinator
    tracks_coordinator = entry.runtime_data.tracks_coordinator

    entities: list[SensorEntity] = []
    for bike_id in coordinator.data:
        entities.append(CE04VehicleImageSensor(coordinator, bike_id))
        entities.append(CE04LastUpdateSensor(coordinator, bike_id))
        for description in SENSORS:
            entities.append(CE04Sensor(coordinator, bike_id, description))

        bike = coordinator.data[bike_id]
        if bike and bike.vin:
            entities.append(
                CE04LastRideSensor(tracks_coordinator, bike.vin, bike.vehicle_id)
            )
            entities.append(
                CE04RideStatsSensor(tracks_coordinator, bike.vin, bike.vehicle_id)
            )

    async_add_entities(entities)


# ---------------------------------------------------------------------------
# Recorded tracks (ride history) — separate coordinator, attribute-rich
# ---------------------------------------------------------------------------


class CE04TracksBase(CoordinatorEntity, SensorEntity):
    """Base for ride-history sensors. Attaches to the bike's device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, vin: str, vehicle_id: str | None) -> None:
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_id = vehicle_id

    @property
    def _tracks(self) -> list[RecordedTrack]:
        """Non-deleted rides for this bike (falls back to all if unmatched)."""
        data = self.coordinator.data or []
        if self._vehicle_id:
            matched = [t for t in data if t.bike_id == self._vehicle_id]
            if matched:
                return matched
        return data

    @property
    def device_info(self):
        # Same identifier as the bike's other entities → groups under one device.
        return {"identifiers": {(DOMAIN, self._vin)}}

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success


class CE04LastRideSensor(CE04TracksBase):
    """The most recent ride. State = distance (km); details in attributes."""

    _attr_translation_key = "last_ride"
    _attr_name = "Last ride"
    _attr_icon = "mdi:map-marker-path"
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, vin: str, vehicle_id: str | None) -> None:
        super().__init__(coordinator, vin, vehicle_id)
        self._attr_unique_id = f"{vin.lower()}_last_ride"

    @property
    def _latest(self) -> RecordedTrack | None:
        tracks = [t for t in self._tracks if t.start_time]
        return max(tracks, key=lambda t: t.start_time) if tracks else None

    @property
    def native_value(self):
        latest = self._latest
        return latest.distance_km if latest else None

    @property
    def extra_state_attributes(self):
        lr = self._latest
        if not lr:
            return None
        return {
            "title": lr.title,
            "started": lr.start_time.isoformat() if lr.start_time else None,
            "ended": lr.end_time.isoformat() if lr.end_time else None,
            "ride_time_min": rnd(lr.ride_time_s / 60, 1) if lr.ride_time_s else None,
            "speed_avg_kmh": lr.speed_avg_kmh,
            "speed_max_kmh": lr.speed_max_kmh,
            "lean_left_max_deg": lr.lean_left_max,
            "lean_right_max_deg": lr.lean_right_max,
            "engine_max_rpm": lr.engine_max_rpm,
            "temp_max_c": lr.temp_max_c,
            "temp_min_c": lr.temp_min_c,
            "elevation_max_m": lr.elevation_max_m,
            "elevation_min_m": lr.elevation_min_m,
            "acceleration_max_g": lr.acceleration_max,
            "deceleration_max_g": lr.deceleration_max,
            "start_lat": lr.start_lat,
            "start_lon": lr.start_lon,
            "end_lat": lr.end_lat,
            "end_lon": lr.end_lon,
        }


class CE04RideStatsSensor(CE04TracksBase):
    """Aggregate ride stats. State = ride count; totals in attributes."""

    _attr_translation_key = "ride_stats"
    _attr_name = "Ride stats"
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "rides"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, vin: str, vehicle_id: str | None) -> None:
        super().__init__(coordinator, vin, vehicle_id)
        self._attr_unique_id = f"{vin.lower()}_ride_stats"

    @property
    def native_value(self):
        return len(self._tracks)

    @property
    def extra_state_attributes(self):
        tracks = self._tracks
        if not tracks:
            return None
        now = datetime.now(timezone.utc)
        this_month = sum(
            1
            for t in tracks
            if t.start_time
            and t.start_time.year == now.year
            and t.start_time.month == now.month
        )
        distances = [t.distance_km for t in tracks if t.distance_km is not None]
        speeds = [t.speed_max_kmh for t in tracks if t.speed_max_kmh is not None]
        leans = [
            max(t.lean_left_max or 0, t.lean_right_max or 0)
            for t in tracks
            if t.lean_left_max is not None or t.lean_right_max is not None
        ]
        return {
            "rides_this_month": this_month,
            "total_distance_km": rnd(sum(distances), 1) if distances else 0,
            "longest_ride_km": max(distances) if distances else None,
            "top_speed_kmh": max(speeds) if speeds else None,
            "max_lean_deg": rnd(max(leans), 1) if leans else None,
        }
