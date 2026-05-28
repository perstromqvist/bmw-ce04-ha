from __future__ import annotations

from dataclasses import dataclass
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

from .entity import CE04Entity
from .models import CE04Data


@dataclass(frozen=True, kw_only=True)
class CE04SensorDescription(SensorEntityDescription):
    value_fn: Callable[[CE04Data], object]


SENSORS: tuple[CE04SensorDescription, ...] = (
    # ... (dina befintliga sensorer här) ...
    CE04SensorDescription(
        key="battery_level",
        name="Battery level",
        icon="mdi:battery-charging",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda bike: bike.battery_level,
    ),
    # ... (behåll alla dina övriga sensorer som de var) ...
)


class CE04Sensor(CE04Entity, SensorEntity):
    entity_description: CE04SensorDescription

    def __init__(
        self,
        coordinator,
        bike_id: str,
        description: CE04SensorDescription,
    ) -> None:
        super().__init__(coordinator, bike_id)
        self.entity_description = description
        self._attr_unique_id = f"v1_{self.bike_slug}_{description.key}"
        self._attr_suggested_object_id = f"{self.bike_slug}_{description.key}"

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.bike)

    @property
    def entity_picture(self) -> str | None:
        """Dynamisk bild för hojen utan att kräva ImageEntity-tokens."""
        # Se till att self.bike finns
        if not self.bike or not self.bike.color:
            return "/local/white.png"
            
        raw_color = str(self.bike.color).upper()
        color_map = {
            "P0N3H": "white",
            "P0NB5": "blu",
            "P0N2M": "silver",
        }
        image_name = color_map.get(raw_color, "white")
        return f"/local/{image_name}.png"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = [
        CE04Sensor(coordinator, bike_id, description)
        for bike_id in coordinator.data
        for description in SENSORS
    ]
    async_add_entities(entities)
