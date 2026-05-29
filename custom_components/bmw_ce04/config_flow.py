from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client
import homeassistant.helpers.config_validation as cv

from .api import CE04Client, CE04AuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CE04ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BMW CE 04."""

    VERSION = 1
    MINOR_VERSION = 1

    _reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                client = CE04Client(
                    hass=self.hass,
                    client_id=user_input["client_id"],
                    api_host=user_input["api_host"],
                    auth_host=user_input["auth_host"],
                    poll_interval=user_input.get("poll_interval", 60),
                    verify_ssl=user_input.get("verify_ssl", True),
                )

                # Testa anslutningen och starta device code flow
                verification = await client.async_start_device_flow()

                self.context["client"] = client
                self.context["user_input"] = user_input

                return self.async_show_form(
                    step_id="authorize",
                    description_placeholders={
                        "verification_uri": verification["verification_uri"],
                        "user_code": verification["user_code"],
                        "verification_uri_complete": verification.get(
                            "verification_uri_complete", ""
                        ),
                    },
                )

            except CE04AuthError as err:
                _LOGGER.error("Auth error: %s", err)
                errors["base"] = "authorize_failed"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error")
                errors["base"] = "cannot_connect"

        # Visa initialt formulär
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("client_id"): cv.string,
                    vol.Required("api_host", default="https://api.bmw-motorrad.com"): cv.string,
                    vol.Required("auth_host", default="https://customer.bmw-motorrad.com"): cv.string,
                    vol.Optional("poll_interval", default=60): cv.positive_int,
                    vol.Optional("verify_ssl", default=True): cv.boolean,
                }
            ),
            errors=errors,
        )

    async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle authorization step (after user approved in browser)."""
        client: CE04Client = self.context["client"]
        user_input_data: dict = self.context["user_input"]

        try:
            token = await client.async_complete_device_flow()

            await self.async_set_unique_id(client.get_unique_id())
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="BMW CE 04",
                data={
                    **user_input_data,
                    "token": token.to_dict(),
                },
            )

        except CE04AuthError as err:
            _LOGGER.error("Authorization failed: %s", err)
            return self.async_show_form(
                step_id="authorize",
                errors={"base": "authorize_failed"},
                description_placeholders={
                    "verification_uri": "...",
                    "user_code": "...",
                },
            )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show reauth confirmation and retry."""
        errors: dict[str, str] = {}

        if user_input is not None and self._reauth_entry:
            # Försök ladda om med samma data
            self.hass.config_entries.async_update_entry(
                self._reauth_entry, data=self._reauth_entry.data
            )
            await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            errors=errors,
            description_placeholders={"name": "BMW CE 04"},
        )


class CE04OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "poll_interval",
                        default=self.config_entry.options.get("poll_interval", 60),
                    ): cv.positive_int,
                }
            ),
        )
