from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CE04ApiClient, CE04ApiError, CE04AuthError
from .const import CONF_POLL_INTERVAL, DOMAIN
from .models import CE04Data

_LOGGER = logging.getLogger(__name__)


class CE04Coordinator(DataUpdateCoordinator[dict[str, CE04Data]]):
    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: CE04ApiClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(
                    CONF_POLL_INTERVAL, entry.data[CONF_POLL_INTERVAL]
                )
            ),
        )
        self.entry = entry
        self.client = client

    async def _async_update_data(self) -> dict[str, CE04Data]:
        try:
            bikes = await self.client.async_get_bikes()
        except CE04AuthError as err:
            self.entry.async_start_reauth(self.hass)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except CE04ApiError as err:
            raise UpdateFailed(str(err)) from err
        return {bike.bike_id: bike for bike in bikes}
