from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .entity import CE04Entity

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities([CE04BikeImage(coordinator, bike_id) for bike_id in coordinator.data])

class CE04BikeImage(CE04Entity, ImageEntity):
    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator, bike_id)
        self._attr_name = "Vehicle Image"
        self._attr_unique_id = f"{self.bike_slug}_vehicle_image"

    @property
    def image_url(self) -> str:
        # Hårdkoda en fallback och mappa färger
        raw_color = str(self.bike.color).upper() if self.bike.color else "WHITE"
        color_map = {"P0N3H": "white", "P0NB5": "blu", "P0N2M": "silver"}
        return f"/local/{color_map.get(raw_color, 'white')}.png"

    # DETTA ÄR NYCKELN: Överstyr detta så den inte letar efter tokens
    @property
    def access_tokens(self) -> list[str]:
        return ["none"]
