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
from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN
from .models import CE04Data

_LOGGER = logging.getLogger(__name__)


class CE04Coordinator(DataUpdateCoordinator[dict[str, CE04Data]]):
    """Coordinator responsible for fetching CE04 data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: CE04ApiClient) -> None:
        poll_interval = (
            entry.options.get(CONF_POLL_INTERVAL)
            or entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=poll_interval),
        )

        self.entry = entry
        self.client = client

        _LOGGER.debug("CE04Coordinator initialized with poll interval: %s seconds", poll_interval)

    async def _async_update_data(self) -> dict[str, CE04Data]:
        """Fetch latest CE04 data from BMW CarData."""

        try:
            # Refresh token if needed
            old_token = self.client.token
            await self.client.async_ensure_token()

            # Persist token if changed
            if self.client.token != old_token:
                _LOGGER.debug("Token refreshed, updating config entry")
                new_data = dict(self.entry.data)
                new_data["token"] = self.client.token.as_storage_dict()
                self.hass.config_entries.async_update_entry(self.entry, data=new_data)

            # Fetch bikes
            bikes = await self.client.async_get_bikes()

            # Optional debug dump (only if file already exists)
            dump_path = os.path.join(self.hass.config.config_dir, "bmw_ce04_raw_debug.json")

            def _dump_if_present() -> None:
                if not os.path.exists(dump_path):
                    return
                with open(dump_path, "w", encoding="utf-8") as f:
                    json.dump(
                        [dataclasses.asdict(bike) for bike in bikes],
                        f,
                        indent=4,
                        default=str,
                    )

            await self.hass.async_add_executor_job(_dump_if_present)

        except CE04AuthError as err:
            _LOGGER.warning("Authentication failed, triggering reauth: %s", err)
            self.entry.async_start_reauth(self.hass)
            raise UpdateFailed(f"Authentication failed: {err}") from err

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Network error while updating CE04 data: %s", err)
            raise UpdateFailed(f"Network error: {err}") from err

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
                result[bike.bike_id] = bike   # inte CE04Data.from_api(bike)
            except Exception as err:
                _LOGGER.warning("Failed to store CE04 bike data: %s", err)
        
        return result
