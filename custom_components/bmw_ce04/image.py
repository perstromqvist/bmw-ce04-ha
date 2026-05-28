from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
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

        self._update_image_url()

    def _update_image_url(self) -> None:
        """Uppdatera bild-URL baserat på motorcykelns färg."""
        if not self.bike or not self.bike.color:
            self._attr_image_url = "/local/white.png"
            return

        raw_color = str(self.bike.color).upper()

        # Färgmapning från BMW:s kod till filnamn
        color_map = {
            "P0N3H": "white",
            "P0NB5": "blue",
            "P0N2M": "silver",
            # Lägg till fler färgkoder här vid behov
        }

        color_name = color_map.get(raw_color, "white")  # default till white
        self._attr_image_url = f"/local/{color_name}.png"

    @property
    def image_url(self) -> str | None:
        """Return the image URL."""
        self._update_image_url()   # Uppdatera vid behov
        return self._attr_image_url

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        self._update_image_url()
