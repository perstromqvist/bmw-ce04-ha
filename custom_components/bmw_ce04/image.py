from __future__ import annotations
from homeassistant.components.image import ImageEntity
from .entity import CE04Entity

class CE04BikeImage(CE04Entity, ImageEntity):
    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator, bike_id)
        self._attr_name = "Vehicle Image"
        self._attr_unique_id = f"{self.bike_slug}_vehicle_image"

    @property
    def image_url(self) -> str | None:
        raw_color = str(self.bike.color).upper() if self.bike.color else ""
        color_map = {
            "P0N3H": "white",
            "P0NB5": "blu",
            "P0N2M": "silver",
        }
        image_name = color_map.get(raw_color, "white")
        return f"/local/{image_name}.png"
