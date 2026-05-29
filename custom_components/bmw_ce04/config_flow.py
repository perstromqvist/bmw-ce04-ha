from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CE04ApiClient, CE04AuthError
from .const import (
    CONF_API_HOST,
    CONF_AUTH_HOST,
    CONF_CLIENT_ID,
    CONF_COUNTRY,
    CONF_POLL_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_API_HOST,
    DEFAULT_AUTH_HOST,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    MIN_POLL_INTERVAL,
    MAX_POLL_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class CE04ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._user_input: dict[str, Any] | None = None
        self._device_code: str | None = None
        self._verification_uri: str | None = None
        self._verification_uri_complete: str | None = None
        self._user_code: str | None = None
        self._code_verifier: str | None = None
        self._reauth_entry: config_entries.ConfigEntry | None = None

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _create_client(self, data: dict[str, Any]) -> CE04ApiClient:
        return CE04ApiClient(
            async_get_clientsession(self.hass),
            client_id=data[CONF_CLIENT_ID],
            api_host=data[CONF_API_HOST],
            auth_host=data[CONF_AUTH_HOST],
            country=data[CONF_COUNTRY],
            verify_ssl=data[CONF_VERIFY_SSL],
        )

    # ---------------------------------------------------------
    # User setup
    # ---------------------------------------------------------

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input = dict(user_input)
            user_input[CONF_CLIENT_ID] = user_input[CONF_CLIENT_ID].strip().lower()
            user_input[CONF_COUNTRY] = "en-EN"

            # Validate poll interval
            poll = user_input[CONF_POLL_INTERVAL]
            if poll < MIN_POLL_INTERVAL or poll > MAX_POLL_INTERVAL:
                errors["base"] = "invalid_poll_interval"
            else:
                self._user_input = user_input

                await self.async_set_unique_id(user_input[CONF_CLIENT_ID], raise_on_progress=False)
                self._abort_if_unique_id_configured()

                client = self._create_client(user_input)

                try:
                    code = await client.async_request_device_code()
                except CE04AuthError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    errors["base"] = "cannot_connect"
                else:
                    self._device_code = code.device_code
                    self._verification_uri = code.verification_uri
                    self._verification_uri_complete = code.verification_uri_complete
                    self._user_code = code.user_code
                    self._code_verifier = code.code_verifier
                    return await self.async_step_authorize()

        schema = vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_API_HOST, default=DEFAULT_API_HOST): str,
                vol.Required(CONF_AUTH_HOST, default=DEFAULT_AUTH_HOST): str,
                vol.Required(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): int,
                vol.Required(CONF_VERIFY_SSL, default=True): bool,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    # ---------------------------------------------------------
    # Authorization step
    # ---------------------------------------------------------

    async def async_step_authorize(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        placeholders = {
            "verification_uri": self._verification_uri or "",
            "verification_uri_complete": self._verification_uri_complete or "",
            "user_code": self._user_code or "",
        }

        if user_input is not None:
            client = self._create_client(self._user_input)

            try:
                token = await client.async_exchange_device_code(
                    self._device_code, self._code_verifier
                )
            except CE04AuthError:
                errors["base"] = "authorize_failed"
            except Exception:
                errors["base"] = "authorize_failed"
            else:
                data = dict(self._user_input)
                data["token"] = token.as_storage_dict()
                return self.async_create_entry(title="BMW CE 04", data=data)

        return self.async_show_form(
            step_id="authorize",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders=placeholders,
        )

    # ---------------------------------------------------------
    # Reauthentication
    # ---------------------------------------------------------

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Start reauth flow."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        self._user_input = dict(self._reauth_entry.data)
        return await self.async_step_authorize()

    async def async_step_reauth_confirm(self, user_input=None) -> FlowResult:
        """Confirm reauth."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")

        return await self.async_step_authorize()
