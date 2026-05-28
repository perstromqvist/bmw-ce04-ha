from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
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
    value_fn: Callable[[CE04Data], bool]


BINARY_SENSORS: tuple[CE04BinarySensorDescription, ...] = (
    # CE 04 is EV — alert on battery, not fuel
    CE04BinarySensorDescription(
        key="low_battery",
        name="Low battery",
        icon="mdi:battery-alert",
        value_fn=lambda bike: (bike.battery_level or 100) <= 20,
    ),
    CE04BinarySensorDescription(
        key="front_tire_pressure_low",
        name="Front tire pressure low",
        icon="mdi:car-tire-alert",
        # CE 04 spec: front 2.5 bar, warn below 2.3
        value_fn=lambda bike: (bike.tire_pressure_front_bar or 0) < 2.3,
    ),
    CE04BinarySensorDescription(
        key="rear_tire_pressure_low",
        name="Rear tire pressure low",
        icon="mdi:car-tire-alert",
        # CE 04 spec: rear 2.9 bar, warn below 2.6
        value_fn=lambda bike: (bike.tire_pressure_rear_bar or 0) < 2.6,
    ),
    CE04BinarySensorDescription(
        key="service_due_soon",
        name="Service due soon",
        icon="mdi:wrench",
        value_fn=lambda bike: (
            bike.next_service_remaining_distance_km or 999999
        ) < 1000,
    ),
)


class CE04BinarySensor(CE04Entity, BinarySensorEntity):
    entity_description: CE04BinarySensorDescription

    def __init__(
        self,
        coordinator,
        bike_id: str,
        description: CE04BinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, bike_id)
        self.entity_description = description
        self._attr_unique_id = f"v1_{self.bike_slug}_{description.key}"
        self._attr_suggested_object_id = f"{self.bike_slug}_{description.key}"

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.bike)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities: list[BinarySensorEntity] = [
        CE04BinarySensor(coordinator, bike_id, description)
        for bike_id in coordinator.data
        for description in BINARY_SENSORS
    ]
    async_add_entities(entities)
