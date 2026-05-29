from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import CONF_CLIENT_ID, CONF_API_HOST, CONF_AUTH_HOST, CONF_COUNTRY, CONF_POLL_INTERVAL, CONF_VERIFY_SSL


def _redact_entry_data(data: dict) -> dict:
    """Return entry data with token stripped out."""
    return {
        CONF_CLIENT_ID: data.get(CONF_CLIENT_ID),
        CONF_API_HOST: data.get(CONF_API_HOST),
        CONF_AUTH_HOST: data.get(CONF_AUTH_HOST),
        CONF_COUNTRY: data.get(CONF_COUNTRY),
        CONF_POLL_INTERVAL: data.get(CONF_POLL_INTERVAL),
        CONF_VERIFY_SSL: data.get(CONF_VERIFY_SSL),
        "token_present": "token" in data,
    }


def _anon_vin(vin: str | None) -> str | None:
    if not vin:
        return None
    return f"***{vin[-6:]}"


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator

    bikes = {}
    for bike_id, bike in coordinator.data.items():
        bikes[bike_id] = {
            "vin": _anon_vin(bike.vin),
            "name": bike.name,
            "type_key": bike.type_key,
            "color": bike.color,
            "battery_level": bike.battery_level,
            "remaining_range_km": bike.remaining_range_electric_km,
            "total_mileage_km": bike.total_mileage_km,
            "last_connected_time": str(bike.last_connected_time),
            "latitude_present": bike.latitude is not None,
            "longitude_present": bike.longitude is not None,
        }

    return {
        "entry_data": _redact_entry_data(entry.data),
        "entry_options": _redact_entry_data(entry.options) if entry.options else {},
        "bikes": bikes,
    }
