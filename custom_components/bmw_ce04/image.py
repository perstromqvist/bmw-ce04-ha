from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COLOR_MAP, DEFAULT_COLOR
from .entity import CE04Entity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BMW CE 04 image entities."""
    coordinator = entry.runtime_data.coordinator

    async_add_entities(
        CE04BikeImage(coordinator, bike_id)
        for bike_id in coordinator.data
    )


class CE04BikeImage(CE04Entity, ImageEntity):
    """Image entity for BMW CE 04 vehicle."""

    _attr_has_entity_name = True
    _attr_translation_key = "vehicle_image"

    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator, bike_id)
        self._attr_unique_id = f"{self.bike_slug}_vehicle_image"
        self._attr_suggested_object_id = "vehicle_image"
        self._attr_image_url = self._resolve_image_url()

    def _resolve_image_url(self) -> str:
        """Return the correct image URL based on the bike's color code."""
        color_code = self.bike.color if self.bike else None
        color_name = COLOR_MAP.get(color_code, DEFAULT_COLOR) if color_code else DEFAULT_COLOR
        return f"/local/{color_name}.jpg"

    def _handle_coordinator_update(self) -> None:
        """Update image URL when coordinator pushes new data."""
        self._attr_image_url = self._resolve_image_url()
        super()._handle_coordinator_update()
