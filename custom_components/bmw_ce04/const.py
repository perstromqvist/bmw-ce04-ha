from __future__ import annotations

# ---------------------------------------------------------------------------
# Domain & Platforms
# ---------------------------------------------------------------------------

DOMAIN = "bmw_ce04"
LOGGER_NAME = DOMAIN

PLATFORMS = ["sensor", "binary_sensor", "device_tracker"]

# ---------------------------------------------------------------------------
# Configuration keys
# ---------------------------------------------------------------------------

CONF_CLIENT_ID = "client_id"
CONF_COUNTRY = "country"
CONF_API_HOST = "api_host"
CONF_AUTH_HOST = "auth_host"
CONF_POLL_INTERVAL = "poll_interval"
CONF_TRACKS_POLL_INTERVAL = "tracks_poll_interval"
CONF_VERIFY_SSL = "verify_ssl"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_API_HOST = "https://api.connectedride.bmwgroup.com"
DEFAULT_AUTH_HOST = "https://customer.bmwgroup.com"
DEFAULT_COUNTRY = "en-EN"  # no longer used in the bikes URL; kept for compatibility
DEFAULT_POLL_INTERVAL = 1800  # 30 min ≈ 48 calls/day, under BMW's documented 50/24h quota
DEFAULT_VERIFY_SSL = True

MIN_POLL_INTERVAL = 600
MAX_POLL_INTERVAL = 3600

# Recorded tracks change rarely (only after a ride), so they poll on their own,
# much slower schedule. Default 3 h; configurable between 30 min and 24 h.
DEFAULT_TRACKS_POLL_INTERVAL = 10800  # 3 hours
MIN_TRACKS_POLL_INTERVAL = 1800       # 30 min
MAX_TRACKS_POLL_INTERVAL = 86400      # 24 h

# ---------------------------------------------------------------------------
# Attributes
# ---------------------------------------------------------------------------

ATTR_BIKE_ID = "bike_id"
ATTR_RAW = "raw"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"

# ---------------------------------------------------------------------------
# Device Info
# ---------------------------------------------------------------------------

MANUFACTURER = "BMW Motorrad"
MODEL = "CE 04"

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

DEVICE_CODE_ENDPOINT = "/gcdm/oauth/device/code"
TOKEN_ENDPOINT = "/gcdm/oauth/token"
# BMW moved the bike data from cpp.bmw-motorrad.com to the ConnectedRide
# CloudSync API. No country segment any more; a limit query param instead.
BIKES_ENDPOINT_TMPL = "/cnrd/cloudsync/v2/bikes?limit=200"
# Recorded rides (trip history). Same auth/headers as bikes; wrapper key is
# the lowercase "recordedtracks".
TRACKS_ENDPOINT = "/cnrd/cloudsync/v2/recordedTracks?limit=200"

# ---------------------------------------------------------------------------
# App-identifying headers
# ---------------------------------------------------------------------------
# The CloudSync endpoint expects requests that look like the BMW Motorrad
# Connected app. These mirror the app's headers. If BMW starts rejecting an old
# client version, bump these to match a current app build.

APP_CLIENT_VERSION = "5.10.0 (51000002)"
APP_CLIENT_BUILD = "51000002"
APP_USER_AGENT = "Connected/51000002 CFNetwork/3860.600.12 Darwin/25.5.0"
APP_DEVICE_TYPE = "ios"
APP_DEVICE_OS_VERSION = "26.5.0"
APP_ACCEPT_LANGUAGE = "en-US,en;q=0.9"

# ---------------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------------

STATIC_PATH = "/api/bmw_ce04/static"
