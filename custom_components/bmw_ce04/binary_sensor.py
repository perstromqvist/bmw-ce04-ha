from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import CE04Entity
from .models import CE04Data


@dataclass(frozen=True, kw_only=True)
class CE04BinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[CE04Data], bool | None]


# How long after the last cloud check-in the scooter still counts as
# "recently connected". The CE 04 phones home sporadically, so a tight
# window flaps on/off — tune this to your bike's check-in cadence.
RECENT_CONNECT_WINDOW = timedelta(hours=6)

# chargingMode values that mean the scooter is actively drawing charge.
# The only sample we have was idle/full (chargingMode = null), so this set
# is a best guess until a real charging sample confirms the string BMW sends.
CHARGING_MODES = {"CHARGING", "ACTIVE", "ON"}


def _is_charging(bike: CE04Data) -> bool:
    """True only when chargingMode clearly indicates active charging."""
    mode = bike.raw.get("chargingMode")
    if mode is True:
        return True
    if isinstance(mode, str) and mode.strip().upper() in CHARGING_MODES:
        return True
    return False


BINARY_SENSORS: tuple[CE04BinarySensorDescription, ...] = (
    # ---------------------------------------------------------
    # Battery
    # ---------------------------------------------------------
    CE04BinarySensorDescription(
        key="low_battery",
        translation_key="low_battery",
        name="Low battery",
        icon="mdi:battery-alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda bike: (
            bike.battery_level is not None and bike.battery_level <= 20
        ),
    ),

    # ---------------------------------------------------------
    # Tire pressure
    # ---------------------------------------------------------
    CE04BinarySensorDescription(
        key="front_tire_pressure_low",
        translation_key="front_tire_pressure_low",
        name="Front tire pressure low",
        icon="mdi:car-tire-alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda bike: (
            bike.tire_pressure_front_bar is not None
            and bike.tire_pressure_front_bar < 2.1
        ),
    ),
    CE04BinarySensorDescription(
        key="rear_tire_pressure_low",
        translation_key="rear_tire_pressure_low",
        name="Rear tire pressure low",
        icon="mdi:car-tire-alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda bike: (
            bike.tire_pressure_rear_bar is not None
            and bike.tire_pressure_rear_bar < 2.3
        ),
    ),

    # ---------------------------------------------------------
    # Service
    # ---------------------------------------------------------
    CE04BinarySensorDescription(
        key="service_due_soon",
        translation_key="service_due_soon",
        name="Service due soon",
        icon="mdi:wrench",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda bike: (
            bike.next_service_remaining_distance_km is not None
            and bike.next_service_remaining_distance_km < 1000
        ),
    ),
    CE04BinarySensorDescription(
        key="service_overdue",
        translation_key="service_overdue",
        name="Service overdue",
        icon="mdi:wrench-clock",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda bike: (
            bike.next_service_remaining_distance_km is not None
            and bike.next_service_remaining_distance_km < 0
        ),
    ),

    # ---------------------------------------------------------
    # Charging
    # ---------------------------------------------------------
    CE04BinarySensorDescription(
        key="charging",
        translation_key="charging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda bike: _is_charging(bike),
    ),

    # ---------------------------------------------------------
    # Connectivity
    # ---------------------------------------------------------
    CE04BinarySensorDescription(
        key="online",
        translation_key="online",
        name="Recently connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda bike: _is_recently_connected(bike.last_connected_time),
    ),
)


def _is_recently_connected(last_connected: datetime | None) -> bool:
    """Return True if the scooter checked in within RECENT_CONNECT_WINDOW."""
    if last_connected is None:
        return False
    return datetime.now(timezone.utc) - last_connected < RECENT_CONNECT_WINDOW


class CE04BinarySensor(CE04Entity, BinarySensorEntity):
    """Representation of a BMW CE 04 binary sensor."""

    entity_description: CE04BinarySensorDescription

    def __init__(
        self, coordinator, bike_id: str, description: CE04BinarySensorDescription
    ) -> None:
        super().__init__(coordinator, bike_id)
        self.entity_description = description
        self._attr_unique_id = f"{self.bike_slug}_{description.key}"
        self._attr_suggested_object_id = f"{self.bike_slug}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        if not self.bike:
            return None
        return self.entity_description.value_fn(self.bike)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMW CE 04 binary sensor entities."""
    coordinator = entry.runtime_data.coordinator

    entities: list[BinarySensorEntity] = [
        CE04BinarySensor(coordinator, bike_id, description)
        for bike_id in coordinator.data
        for description in BINARY_SENSORS
    ]

    async_add_entities(entities)
