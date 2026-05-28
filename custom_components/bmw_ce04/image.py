from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import CE04Entity

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the image platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [CE04BikeImage(coordinator, bike_id) for bike_id in coordinator.data]
    )

class CE04BikeImage(CE04Entity, ImageEntity):
    """Representation of the BMW CE 04 bike image."""

    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator, bike_id)
        self._attr_name = "Vehicle Image"
        self._attr_unique_id = f"{self.bike_slug}_vehicle_image"
        self._attr_suggested_object_id = f"{self.bike_slug}_vehicle_image"

    @property
    def image_url(self) -> str | None:
        """Return the URL of the image based on bike color."""
        if not self.bike or not self.bike.color:
            return "/local/white.png" # Fallback
            
        raw_color = str(self.bike.color).upper()
        color_map = {
            "P0N3H": "white",
            "P0NB5": "blu",
            "P0N2M": "silver",
        }
        image_name = color_map.get(raw_color, "white")
        return f"/local/{image_name}.png"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {"color_code": self.bike.color}

    # VIKTIGT: För att ImageEntity inte ska krascha vid sök efter access_tokens,
    # tvingar vi den att använda vår image_url genom att inte sätta 
    # de interna token-attributen.
    @property
    def state(self) -> str | None:
        return self.image_url
