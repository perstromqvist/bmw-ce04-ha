from __future__ import annotations

import dataclasses
import json
import logging
import os
import asyncio
import aiohttp
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CE04ApiClient, CE04ApiError, CE04AuthError
from .const import CONF_POLL_INTERVAL, DOMAIN
from .models import CE04Data

_LOGGER = logging.getLogger(__name__)


class CE04Coordinator(DataUpdateCoordinator[dict[str, CE04Data]]):
    """Coordinator responsible for fetching CE04 data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: CE04ApiClient) -> None:
        poll_interval = entry.options.get(CONF_POLL_INTERVAL, entry.data[CONF_POLL_INTERVAL])

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=poll_interval),
        )

        self.entry = entry
        self.client = client

    async def _async_update_data(self) -> dict[str, CE04Data]:
        """Fetch latest CE04 data from BMW CarData."""

        try:
            # Refresh token if needed (non-invasive)
            await self.client.async_refresh_token_if_needed()

            # Fetch bikes
            bikes = await self.client.async_get_bikes()

            # DEBUG: dump raw data to file — intentionally kept
            dump_path = os.path.join(self.hass.config.config_dir, "bmw_ce04_raw_debug.json")

            def _dump():
                with open(dump_path, "w", encoding="utf-8") as f:
                    json.dump(
                        [dataclasses.asdict(bike) for bike in bikes],
                        f,
                        indent=4,
                        default=str,
                    )

            await self.hass.async_add_executor_job(_dump)

        except CE04AuthError as err:
            # Keep your existing reauth behavior
            self.entry.async_start_reauth(self.hass)
            raise UpdateFailed(f"Authentication failed: {err}") from err

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Network error while updating CE04 data: %s", err)
            raise UpdateFailed("Network error") from err

        except CE04ApiError as err:
            _LOGGER.error("API error while updating CE04 data: %s", err)
            raise UpdateFailed(str(err)) from err

        except Exception as err:
            _LOGGER.exception("Unexpected error updating CE04 data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

        # Convert raw API → CE04Data models
        result: dict[str, CE04Data] = {}

        for bike in bikes:
            try:
                result[bike.bike_id] = CE04Data.from_api(bike)
            except Exception as err:
                _LOGGER.warning("Failed to parse CE04 bike data: %s", err)

        return result
