from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL


class CE04Entity(CoordinatorEntity):
    """Base class for all CE04 entities."""

    def __init__(self, coordinator, bike_id: str) -> None:
        super().__init__(coordinator)
        self._bike_id = bike_id

    # ---------------------------------------------------------
    # Access to the bike data
    # ---------------------------------------------------------
    @property
    def bike(self):
        """Return the CE04Data object for this bike."""
        return self.coordinator.data.get(self._bike_id)

    @property
    def bike_slug(self) -> str:
        """Short slug used for unique IDs and object IDs."""
        if not self.bike or not self.bike.vin:
            return "ce04"
        return self.bike.vin.lower()

    # ---------------------------------------------------------
    # Device Info (shown in HA device registry)
    # ---------------------------------------------------------
    @property
    def device_info(self):
        """Return device information for the CE04."""
        if not self.bike:
            return None

        vin = self.bike.vin or "unknown"

        return {
            "identifiers": {(DOMAIN, vin)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": f"{MODEL} ({vin[-6:]})",
            "sw_version": None,  # API doesn't expose firmware yet
        }

    # ---------------------------------------------------------
    # Availability
    # ---------------------------------------------------------
    @property
    def available(self) -> bool:
        """Available only when the last poll succeeded and this bike has data."""
        return self.coordinator.last_update_success and self.bike is not None
