from __future__ import annotations

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import CE04Entity


class CE04Tracker(CE04Entity, TrackerEntity):
    """GPS tracker entity for the CE 04."""

    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator, bike_id)
        self._attr_unique_id = f"v1_{self.bike_slug}_location"
        self._attr_suggested_object_id = f"{self.bike_slug}_location"
        self._attr_name = "Location"
        self._attr_icon = "mdi:map-marker"

    @property
    def latitude(self) -> float | None:
        return self.bike.latitude

    @property
    def longitude(self) -> float | None:
        return self.bike.longitude

    @property
    def source_type(self) -> str:
        from homeassistant.components.device_tracker import SourceType
        return SourceType.GPS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    entities = [
        CE04Tracker(coordinator, bike_id) for bike_id in coordinator.data
    ]
    async_add_entities(entities)
