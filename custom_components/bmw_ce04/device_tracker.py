from __future__ import annotations

from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import CE04Entity


class CE04Tracker(CE04Entity, TrackerEntity):
    """GPS tracker entity for the CE 04."""

    _attr_source_type = SourceType.GPS
    _attr_icon = "mdi:map-marker"

    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator, bike_id)
        self._attr_unique_id = f"{self.bike_slug}_location"
        self._attr_suggested_object_id = f"{self.bike_slug}_location"

    @property
    def name(self) -> str:
        if not self.bike:
            return "CE04 Location"
        return f"CE04 {self.bike.vin[-6:]} Location"

    @property
    def latitude(self) -> float | None:
        if not self.bike:
            return None
        return self.bike.latitude

    @property
    def longitude(self) -> float | None:
        if not self.bike:
            return None
        return self.bike.longitude

    @property
    def extra_state_attributes(self) -> dict:
        if not self.bike:
            return {}
        return {
            "vin": self.bike.vin,
            "last_connected": self.bike.last_connected_time,
            "raw_latitude": self.bike.latitude,
            "raw_longitude": self.bike.longitude,
        }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator

    entities = [
        CE04Tracker(coordinator, bike_id)
        for bike_id in coordinator.data
    ]

    async_add_entities(entities)
