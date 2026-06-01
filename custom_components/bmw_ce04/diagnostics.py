from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_CLIENT_ID

# Keys whose values are masked before diagnostics are shown or shared.
# Everything else — including the full vehicle telemetry — is left intact, so a
# downloaded report is safe to post publicly when asking for help.
TO_REDACT = {
    CONF_CLIENT_ID,
    "token",
    "vin",
    "vehicleId",
    "hashedShortVin",
    "hashedLongVin",
    "itemId",
    "lastConnectedLat",
    "lastConnectedLon",
    "latitude",
    "longitude",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry, including the full raw payload.

    Sensitive identifiers (VIN, vehicle/account IDs, GPS, token, client ID) are
    redacted; every other field, including the complete raw API response for each
    bike, is included verbatim for troubleshooting.
    """
    coordinator = entry.runtime_data.coordinator

    bikes: dict[str, dict] = {}
    for index, bike in enumerate(coordinator.data.values(), start=1):
        bikes[f"bike_{index}"] = {
            # A short, human-readable summary of the parsed model...
            "parsed": {
                "name": bike.name,
                "type_key": bike.type_key,
                "color": bike.color,
                "battery_level": bike.battery_level,
                "remaining_range_electric_km": bike.remaining_range_electric_km,
                "total_mileage_km": bike.total_mileage_km,
                "next_service_due_date": str(bike.next_service_due_date),
                "last_connected_time": str(bike.last_connected_time),
            },
            # ...plus the complete, unmodified API response (redacted below).
            "raw": bike.raw,
        }

    return async_redact_data(
        {
            "entry_data": dict(entry.data),
            "entry_options": dict(entry.options),
            "bikes": bikes,
        },
        TO_REDACT,
    )
