from __future__ import annotations

import logging
import json  # Tillagt för att spara JSON
import os    # Tillagt för filhantering
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
            
            # --- DEBUG: Spara rådata till en fil ---
            # Vi sparar datan i config-mappen så den är lätt att nå via VS Code
            dump_path = os.path.join(self.hass.config.config_dir, "bmw_ce04_raw_debug.json")
            
            # Vi konverterar bike-objekten till en enkel lista av dictionaries för att kunna spara som JSON
            # Om din CE04Data har en __dict__ eller as_dict metod, använd den
            raw_data_to_save = [bike.__dict__ for bike in bikes] 
            
            with open(dump_path, "w", encoding="utf-8") as f:
                json.dump(raw_data_to_save, f, indent=4)
            # --------------------------------------

        except CE04AuthError as err:
            self.entry.async_start_reauth(self.hass)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except CE04ApiError as err:
            raise UpdateFailed(str(err)) from err
            
        return {bike.bike_id: bike for bike in bikes}
