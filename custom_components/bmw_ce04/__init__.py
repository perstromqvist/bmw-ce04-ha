from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CE04ApiClient, TokenData
from .const import (
    CONF_API_HOST,
    CONF_AUTH_HOST,
    CONF_CLIENT_ID,
    CONF_COUNTRY,
    CONF_POLL_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    DEFAULT_COUNTRY,
    PLATFORMS,
)
from .coordinator import CE04Coordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeData:
    """Runtime data for the integration."""
    client: CE04ApiClient
    coordinator: CE04Coordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BMW CE 04 integration."""
    _LOGGER.debug("Setting up BMW CE 04 entry %s", entry.entry_id)

    session = async_get_clientsession(hass)

    client = CE04ApiClient(
        session,
        client_id=entry.data[CONF_CLIENT_ID],
        api_host=entry.data[CONF_API_HOST],
        auth_host=entry.data[CONF_AUTH_HOST],
        country=entry.data.get(CONF_COUNTRY, DEFAULT_COUNTRY),
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, True),
    )

    # Load stored token if available
    if token_data := entry.data.get("token"):
        client.set_token(TokenData.from_token_response(token_data))

    coordinator = CE04Coordinator(hass, entry, client)

    # First data fetch
    await coordinator.async_config_entry_first_refresh()

    # Save runtime objects
    entry.runtime_data = RuntimeData(client=client, coordinator=coordinator)

    # Register services (safely - only once)
    await _async_register_services(hass)

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register services once per integration load."""
    if hass.services.has_service(DOMAIN, "force_update"):
        return  # Already registered

    async def handle_force_update(call: ServiceCall):
        """Force an immediate update."""
        bike_id = call.data.get("bike_id")
        _LOGGER.info("Service force_update called (bike_id=%s)", bike_id)

        coordinator = _get_coordinator_from_call(hass, call)
        if not coordinator:
            return

        await coordinator.async_request_refresh()

    async def handle_export_raw(call: ServiceCall):
        """Export raw API data for debugging."""
        bike_id = call.data.get("bike_id")
        _LOGGER.info("Service export_raw_data called (bike_id=%s)", bike_id)

        coordinator = _get_coordinator_from_call(hass, call)
        if not coordinator:
            return

        if bike_id:
            bike = coordinator.data.get(bike_id)
            return bike.raw if bike else None
        return {bid: b.raw for bid, b in coordinator.data.items()}

    async def handle_clear_debug(call: ServiceCall):
        """Delete the debug dump file if it exists."""
        dump_path = os.path.join(hass.config.config_dir, "bmw_ce04_raw_debug.json")
        _LOGGER.info("Service clear_debug_dump called")

        if os.path.exists(dump_path):
            try:
                os.remove(dump_path)
                _LOGGER.info("Deleted debug dump file: %s", dump_path)
                return True
            except Exception as err:
                _LOGGER.error("Failed to delete debug dump: %s", err)
                return False
        return True

    hass.services.async_register(DOMAIN, "force_update", handle_force_update)
    hass.services.async_register(DOMAIN, "export_raw_data", handle_export_raw)
    hass.services.async_register(DOMAIN, "clear_debug_dump", handle_clear_debug)


def _get_coordinator_from_call(hass: HomeAssistant, call: ServiceCall):
    """Helper to get coordinator from any entry (multi-entry support)."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.runtime_data and hasattr(entry.runtime_data, "coordinator"):
            return entry.runtime_data.coordinator
    return None


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload BMW CE 04 integration."""
    _LOGGER.debug("Unloading BMW CE 04 entry %s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Remove services when last entry is unloaded
        if len(hass.config_entries.async_entries(DOMAIN)) <= 1:
            hass.services.async_remove(DOMAIN, "force_update")
            hass.services.async_remove(DOMAIN, "export_raw_data")
            hass.services.async_remove(DOMAIN, "clear_debug_dump")

        entry.runtime_data = None

    return unload_ok
