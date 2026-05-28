from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import ATTR_BIKE_ID, ATTR_RAW, DOMAIN


class CE04Entity(CoordinatorEntity):
    """Base entity for BMW CE 04."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator)
        self._bike_id = bike_id

    @property
    def bike(self):
        return self.coordinator.data[self._bike_id]

    @property
    def bike_name(self) -> str:
        return self.bike.name or "BMW CE 04"

    @property
    def bike_slug(self) -> str:
        return slugify(self.bike_name)

    @property
    def device_info(self) -> DeviceInfo:
        bike = self.bike

        model_parts: list[str] = ["CE 04"]
        if bike.type_key:
            model_parts.append(f"({bike.type_key})")
        if bike.color:
            model_parts.append(bike.color)

        model = " ".join(model_parts)

        sw_version = None
        if bike.raw.get("_version") is not None:
            sw_version = str(bike.raw.get("_version"))

        return DeviceInfo(
            identifiers={(DOMAIN, self._bike_id)},
            manufacturer="BMW Motorrad",
            name=self.bike_name,
            model=model,
            serial_number=bike.vin or self._bike_id,
            sw_version=sw_version,
        )

    @property
    def available(self) -> bool:
        return (
            self._bike_id in self.coordinator.data
            and self.coordinator.last_update_success
        )

    @property
    def extra_state_attributes(self) -> dict:
        bike = self.bike
        attrs: dict = {
            ATTR_BIKE_ID: self._bike_id,
            ATTR_RAW: bike.raw,
        }
        if bike.vin:
            attrs["vin"] = bike.vin
        if bike.type_key:
            attrs["type_key"] = bike.type_key
        if bike.color:
            attrs["color"] = bike.color
        return attrs
