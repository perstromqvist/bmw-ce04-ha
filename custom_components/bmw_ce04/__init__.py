from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CE04ApiClient, TokenData
from .const import (
    CONF_API_HOST,
    CONF_AUTH_HOST,
    CONF_CLIENT_ID,
    CONF_COUNTRY,
    CONF_VERIFY_SSL,
    DEFAULT_API_HOST,
    DEFAULT_AUTH_HOST,
    DEFAULT_COUNTRY,
    DOMAIN,
    PLATFORMS,
    STATIC_PATH,
)
from .coordinator import CE04Coordinator, CE04TracksCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeData:
    """Runtime data for the integration."""
    client: CE04ApiClient
    coordinator: CE04Coordinator
    tracks_coordinator: CE04TracksCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BMW CE 04 integration."""
    _LOGGER.debug("Setting up BMW CE 04 entry %s", entry.entry_id)

    await _async_register_static_path(hass)

    session = async_get_clientsession(hass)

    # Migrate existing entries: BMW moved the bike data off cpp.bmw-motorrad.com
    # to the ConnectedRide CloudSync API. Older config entries still have the old
    # host stored, so update them in place (no re-add needed).
    api_host = entry.data.get(CONF_API_HOST, DEFAULT_API_HOST)
    if not api_host or "cpp.bmw-motorrad.com" in api_host:
        api_host = DEFAULT_API_HOST
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_API_HOST: DEFAULT_API_HOST}
        )
        _LOGGER.info("Migrated API host to %s", DEFAULT_API_HOST)

    client = CE04ApiClient(
        session,
        client_id=entry.data[CONF_CLIENT_ID],
        api_host=api_host,
        auth_host=entry.data.get(CONF_AUTH_HOST, DEFAULT_AUTH_HOST),
        country=entry.data.get(CONF_COUNTRY, DEFAULT_COUNTRY),
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, True),
    )

    if token_data := entry.data.get("token"):
        client.set_token(TokenData.from_token_response(token_data))

    coordinator = CE04Coordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    # Recorded tracks are secondary: refresh without blocking setup, so a tracks
    # hiccup never takes down the whole integration.
    tracks_coordinator = CE04TracksCoordinator(hass, entry, client)
    await tracks_coordinator.async_refresh()

    entry.runtime_data = RuntimeData(
        client=client,
        coordinator=coordinator,
        tracks_coordinator=tracks_coordinator,
    )

    await _async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload on options changes so settings (e.g. poll interval) take effect
    # without restarting Home Assistant.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_static_path(hass: HomeAssistant) -> None:
    """Register www/ folder as static path — once per HA session."""
    if hass.data.get(f"_{DOMAIN}_static_registered"):
        return

    www_path = Path(__file__).parent / "www"
    if await hass.async_add_executor_job(www_path.is_dir):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_PATH, str(www_path), cache_headers=True)]
        )
        _LOGGER.debug("Registered static path %s -> %s", STATIC_PATH, www_path)

    hass.data[f"_{DOMAIN}_static_registered"] = True


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register services once per integration load."""
    if hass.services.has_service(DOMAIN, "force_update"):
        return

    async def handle_force_update(call: ServiceCall):
        coordinator = _get_coordinator_from_call(hass, call)
        if coordinator:
            await coordinator.async_request_refresh()

    async def handle_export_raw(call: ServiceCall):
        bike_id = call.data.get("bike_id")
        coordinator = _get_coordinator_from_call(hass, call)
        if not coordinator:
            return {}
        if bike_id:
            bike = coordinator.data.get(bike_id)
            return bike.raw if bike else {}
        return {bid: b.raw for bid, b in coordinator.data.items()}

    async def handle_clear_debug(call: ServiceCall):
        dump_path = os.path.join(hass.config.config_dir, "bmw_ce04_raw_debug.json")

        def _remove() -> bool:
            if not os.path.exists(dump_path):
                return True
            try:
                os.remove(dump_path)
                return True
            except Exception as err:
                _LOGGER.error("Failed to delete debug dump: %s", err)
                return False

        return await hass.async_add_executor_job(_remove)

    hass.services.async_register(DOMAIN, "force_update", handle_force_update)
    hass.services.async_register(
        DOMAIN,
        "export_raw_data",
        handle_export_raw,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(DOMAIN, "clear_debug_dump", handle_clear_debug)


def _get_coordinator_from_call(hass: HomeAssistant, call: ServiceCall):
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.runtime_data and hasattr(entry.runtime_data, "coordinator"):
            return entry.runtime_data.coordinator
    return None


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload BMW CE 04 integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        if len(hass.config_entries.async_entries(DOMAIN)) <= 1:
            hass.services.async_remove(DOMAIN, "force_update")
            hass.services.async_remove(DOMAIN, "export_raw_data")
            hass.services.async_remove(DOMAIN, "clear_debug_dump")
            hass.data.pop(f"_{DOMAIN}_static_registered", None)

        entry.runtime_data = None

    return unload_ok
