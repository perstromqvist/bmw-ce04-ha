from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp

from .const import BIKES_ENDPOINT_TMPL, DEVICE_CODE_ENDPOINT, TOKEN_ENDPOINT
from .models import CE04Data

_LOGGER = logging.getLogger(__name__)

TOKEN_EXPIRY_MARGIN = timedelta(seconds=60)


class CE04ApiError(Exception):
    """Base API error."""


class CE04AuthError(CE04ApiError):
    """Authentication failure."""


@dataclass(slots=True)
class DeviceCodeData:
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str | None
    expires_in: int
    interval: int
    code_verifier: str
    code_challenge: str


@dataclass(slots=True)
class TokenData:
    access_token: str
    refresh_token: str | None
    id_token: str | None
    expires_at: datetime

    @classmethod
    def from_token_response(cls, data: dict[str, Any]) -> "TokenData":
        if "expires_at" in data:
            expires_at = datetime.fromisoformat(data["expires_at"])
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
        else:
            expires_in = int(data.get("expires_in", 3600))
            expires_at = datetime.now(tz=UTC) + timedelta(seconds=max(expires_in - 60, 60))

        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            id_token=data.get("id_token"),
            expires_at=expires_at,
        )

    def as_storage_dict(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "id_token": self.id_token,
            "expires_at": self.expires_at.isoformat(),
        }


class CE04ApiClient:
    """BMW CarData API client, tuned for the CE 04 electric scooter."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        client_id: str,
        api_host: str,
        auth_host: str,
        country: str,
        verify_ssl: bool,
    ) -> None:
        self._session = session
        self._client_id = client_id.strip().lower()
        self._api_host = api_host.rstrip("/")
        self._auth_host = auth_host.rstrip("/")
        self._country = country
        self._verify_ssl = verify_ssl
        self._token: TokenData | None = None

    @property
    def token(self) -> TokenData | None:
        return self._token

    def set_token(self, token: TokenData | None) -> None:
        self._token = token

    # ------------------------------------------------------------------
    # PKCE helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_code_verifier() -> str:
        return secrets.token_urlsafe(64)

    @staticmethod
    def _generate_code_challenge(verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    # ------------------------------------------------------------------
    # Device-code flow
    # ------------------------------------------------------------------

    async def async_request_device_code(self) -> DeviceCodeData:
        url = f"{self._auth_host}{DEVICE_CODE_ENDPOINT}"
        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)

        payload = {
            "client_id": self._client_id,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        _LOGGER.debug("CE04 device-code request url=%s", url)

        try:
            async with self._session.post(
                url,
                json=payload,
                headers=headers,
                ssl=self._verify_ssl,
            ) as resp:
                text = await resp.text()
                _LOGGER.debug("CE04 device-code status=%s body=%s", resp.status, text)

                if resp.status >= 400:
                    raise CE04AuthError(
                        f"Device code request failed: {resp.status} {text}"
                    )

                data = await resp.json(content_type=None)

                return DeviceCodeData(
                    device_code=data["device_code"],
                    user_code=data["user_code"],
                    verification_uri=data["verification_uri"],
                    verification_uri_complete=data.get("verification_uri_complete"),
                    expires_in=int(data.get("expires_in", 600)),
                    interval=int(data.get("interval", 5)),
                    code_verifier=code_verifier,
                    code_challenge=code_challenge,
                )

        except CE04AuthError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Network error during device-code request: %s", err)
            raise CE04AuthError(f"Device code request network error: {err}") from err
        except Exception as err:
            _LOGGER.exception("CE04 device-code request error: %s", err)
            raise CE04AuthError(f"Device code request error: {err}") from err

    async def async_exchange_device_code(
        self, device_code: str, code_verifier: str
    ) -> TokenData:
        url = f"{self._auth_host}{TOKEN_ENDPOINT}"
        payload = {
            "client_id": self._client_id,
            "device_code": device_code,
            "code_verifier": code_verifier,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "response_type": "device_code",
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            async with self._session.post(
                url, data=payload, headers=headers, ssl=self._verify_ssl
            ) as resp:
                text = await resp.text()
                _LOGGER.debug("CE04 token exchange status=%s body=%s", resp.status, text)

                if resp.status >= 400:
                    raise CE04AuthError(f"Token exchange failed: {resp.status} {text}")

                data = await resp.json(content_type=None)
                self._token = TokenData.from_token_response(data)
                return self._token

        except CE04AuthError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise CE04AuthError(f"Token exchange network error: {err}") from err
        except Exception as err:
            raise CE04AuthError(f"Token exchange error: {err}") from err

    async def async_refresh_token(self) -> TokenData:
        """Refresh access token using refresh_token."""
        if not self._token or not self._token.refresh_token:
            raise CE04AuthError("No refresh token available")

        url = f"{self._auth_host}{TOKEN_ENDPOINT}"
        payload = {
            "client_id": self._client_id,
            "refresh_token": self._token.refresh_token,
            "grant_type": "refresh_token",
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with self._session.post(
            url, data=payload, headers=headers, ssl=self._verify_ssl
        ) as resp:
            text = await resp.text()
            _LOGGER.debug("CE04 refresh token status=%s body=%s", resp.status, text)

            if resp.status >= 400:
                raise CE04AuthError(f"Token refresh failed: {resp.status} {text}")

            data = await resp.json(content_type=None)
            self._token = TokenData.from_token_response(data)
            return self._token

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    async def async_ensure_token(self) -> None:
        """Ensure a valid token exists, refreshing proactively if near expiry."""
        if not self._token:
            raise CE04AuthError("Not authenticated")
        if self._token.expires_at <= datetime.now(tz=UTC) + TOKEN_EXPIRY_MARGIN:
            await self.async_refresh_token()

    # ------------------------------------------------------------------
    # Data fetch
    # ------------------------------------------------------------------

    async def async_get_bikes(self) -> list[CE04Data]:
        await self.async_ensure_token()
        url = f"{self._api_host}{BIKES_ENDPOINT_TMPL.format(country=self._country)}"
        headers = {
            "Authorization": f"Bearer {self._token.access_token}",
            "Accept": "application/json",
        }

        _LOGGER.debug("CE04 bikes request url=%s", url)

        try:
            async with self._session.get(url, headers=headers, ssl=self._verify_ssl) as resp:
                text = await resp.text()
                _LOGGER.debug("CE04 bikes status=%s body=%s", resp.status, text)

                if resp.status == 401:
                    _LOGGER.debug("401 from bikes endpoint, forcing token refresh")
                    await self.async_refresh_token()
                    headers["Authorization"] = f"Bearer {self._token.access_token}"

                    async with self._session.get(
                        url, headers=headers, ssl=self._verify_ssl
                    ) as retry_resp:
                        retry_text = await retry_resp.text()
                        _LOGGER.debug(
                            "CE04 bikes retry status=%s body=%s",
                            retry_resp.status,
                            retry_text,
                        )
                        if retry_resp.status >= 400:
                            raise CE04AuthError(
                                f"Unauthorized after refresh: {retry_resp.status} {retry_text}"
                            )
                        data = await retry_resp.json(content_type=None)
                        return self._parse_bikes(data)

                if resp.status >= 400:
                    raise CE04ApiError(f"Bike fetch failed: {resp.status} {text}")

                data = await resp.json(content_type=None)
                return self._parse_bikes(data)

        except (CE04ApiError, CE04AuthError):
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise CE04ApiError(f"Network error fetching bikes: {err}") from err
        except Exception as err:
            raise CE04ApiError(f"Unexpected error fetching bikes: {err}") from err

    def _parse_bikes(self, data: Any) -> list[CE04Data]:
        """Parse raw API response into CE04Data objects."""
        if isinstance(data, dict):
            if (
                "bmcUserBikes" in data
                and isinstance(data["bmcUserBikes"], dict)
                and "bikes" in data["bmcUserBikes"]
                and isinstance(data["bmcUserBikes"]["bikes"], list)
            ):
                items = data["bmcUserBikes"]["bikes"]
            elif "items" in data and isinstance(data["items"], list):
                items = data["items"]
            elif "bikes" in data and isinstance(data["bikes"], list):
                items = data["bikes"]
            else:
                items = [data]
        elif isinstance(data, list):
            items = data
        else:
            raise CE04ApiError(f"Unexpected payload type: {type(data)!r}")

        return [CE04Data.from_api(item) for item in items]
