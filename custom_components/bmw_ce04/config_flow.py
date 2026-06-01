from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import CE04ApiClient, CE04AuthError
from .const import (
    CONF_API_HOST,
    CONF_AUTH_HOST,
    CONF_CLIENT_ID,
    CONF_POLL_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_API_HOST,
    DEFAULT_AUTH_HOST,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    MIN_POLL_INTERVAL,
    MAX_POLL_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class CE04ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BMW CE 04."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        self._user_input: dict[str, Any] | None = None
        self._device_code: str | None = None
        self._code_verifier: str | None = None
        self._verification_uri: str | None = None
        self._verification_uri_complete: str | None = None
        self._user_code: str | None = None
        self._reauth_entry: config_entries.ConfigEntry | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CE04OptionsFlow:
        """Return options flow."""
        return CE04OptionsFlow()

    def _build_client(self, data: dict[str, Any]) -> CE04ApiClient:
        return CE04ApiClient(
            async_get_clientsession(self.hass),
            client_id=data[CONF_CLIENT_ID],
            api_host=data[CONF_API_HOST],
            auth_host=data[CONF_AUTH_HOST],
            country="en-EN",
            verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
        )

    # ------------------------------------------------------------------
    # Step 1: user
    # ------------------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Only the Client ID is user-supplied. Hosts, SSL and poll interval
            # use safe defaults so there is nothing here to misconfigure; the
            # poll interval can be adjusted later under Options.
            data = {
                CONF_CLIENT_ID: user_input[CONF_CLIENT_ID].strip().lower(),
                CONF_API_HOST: DEFAULT_API_HOST,
                CONF_AUTH_HOST: DEFAULT_AUTH_HOST,
                CONF_POLL_INTERVAL: DEFAULT_POLL_INTERVAL,
                CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
            }
            client = self._build_client(data)
            try:
                code = await client.async_request_device_code()
            except CE04AuthError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error requesting device code")
                errors["base"] = "cannot_connect"
            else:
                self._user_input = data
                self._device_code = code.device_code
                self._code_verifier = code.code_verifier
                self._verification_uri = code.verification_uri
                self._verification_uri_complete = code.verification_uri_complete or ""
                self._user_code = code.user_code
                return await self.async_step_authorize()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): cv.string,
                }
            ),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Step 2: authorize
    # ------------------------------------------------------------------

    async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle authorization step — user has approved in browser."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = self._build_client(self._user_input)
            try:
                token = await client.async_exchange_device_code(
                    self._device_code, self._code_verifier
                )
            except CE04AuthError:
                errors["base"] = "authorize_failed"
            except Exception:
                _LOGGER.exception("Unexpected error exchanging device code")
                errors["base"] = "authorize_failed"
            else:
                if self._reauth_entry is not None:
                    return self.async_update_reload_and_abort(
                        self._reauth_entry,
                        data={**self._user_input, "token": token.as_storage_dict()},
                    )

                await self.async_set_unique_id(
                    self._user_input[CONF_CLIENT_ID], raise_on_progress=False
                )
                self._abort_if_unique_id_configured()

                data = dict(self._user_input)
                data["token"] = token.as_storage_dict()
                return self.async_create_entry(title="BMW CE 04", data=data)

        return self.async_show_form(
            step_id="authorize",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={
                "verification_uri": self._verification_uri or "",
                "verification_uri_complete": (
                    self._verification_uri_complete
                    or self._verification_uri
                    or ""
                ),
                "user_code": self._user_code or "",
            },
        )

    # ------------------------------------------------------------------
    # Reauth
    # ------------------------------------------------------------------

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        self._user_input = dict(self._reauth_entry.data)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show reauth confirmation, then kick off device code flow again."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = self._build_client(self._user_input)
            try:
                code = await client.async_request_device_code()
            except CE04AuthError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during reauth device code request")
                errors["base"] = "cannot_connect"
            else:
                self._device_code = code.device_code
                self._code_verifier = code.code_verifier
                self._verification_uri = code.verification_uri
                self._verification_uri_complete = code.verification_uri_complete or ""
                self._user_code = code.user_code
                return await self.async_step_authorize()

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"name": "BMW CE 04"},
        )


class CE04OptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_POLL_INTERVAL,
            self.config_entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_POLL_INTERVAL, default=current): vol.All(
                        cv.positive_int,
                        vol.Range(min=MIN_POLL_INTERVAL, max=MAX_POLL_INTERVAL),
                    ),
                }
            ),
        )
