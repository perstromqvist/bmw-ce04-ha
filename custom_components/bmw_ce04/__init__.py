from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CE04ApiClient, TokenData
from .const import (
    CONF_API_HOST,
    CONF_AUTH_HOST,
    CONF_CLIENT_ID,
    CONF_COUNTRY,
    CONF_VERIFY_SSL,
    DOMAIN,
    PLATFORMS,
    DEFAULT_VERIFY_SSL,
)
from .coordinator import CE04Coordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class RuntimeData:
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
        country=entry.data[CONF_COUNTRY],
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )

    # Load stored token
    if token_data := entry.data.get("token"):
        client.set_token(TokenData.from_token_response(token_data))

    coordinator = CE04Coordinator(hass, entry, client)

    # First data fetch
    await coordinator.async_config_entry_first_refresh()

    # Save runtime objects
    entry.runtime_data = RuntimeData(client=client, coordinator=coordinator)

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload BMW CE 04 integration."""
    _LOGGER.debug("Unloading BMW CE 04 entry %s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry.runtime_data = None

    return unload_ok
