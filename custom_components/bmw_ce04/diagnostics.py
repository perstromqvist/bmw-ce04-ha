from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""

    runtime = entry.runtime_data
    coordinator = runtime.coordinator

    # Anonymize VIN
    def _anon_vin(vin: str | None) -> str | None:
        if not vin:
            return None
        return f"***{vin[-6:]}"

    bikes = {}
    for bike_id, bike in coordinator.data.items():
        bikes[bike_id] = {
            "vin": _anon_vin(bike.vin),
            "name": bike.name,
            "type_key": bike.type_key,
            "color": bike.color,
            "battery_level": bike.battery_level,
            "remaining_range_km": bike.remaining_range_electric_km,
            "raw": bike.raw,  # raw API data
        }

    return {
        "entry_data": entry.data,
        "entry_options": entry.options,
        "bikes": bikes,
    }
