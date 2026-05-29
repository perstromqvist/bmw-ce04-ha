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
CONF_VERIFY_SSL = "verify_ssl"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_API_HOST = "https://cpp.bmw-motorrad.com"
DEFAULT_AUTH_HOST = "https://customer.bmwgroup.com"
DEFAULT_COUNTRY = "en-EN"
DEFAULT_POLL_INTERVAL = 300
DEFAULT_VERIFY_SSL = True

MIN_POLL_INTERVAL = 60
MAX_POLL_INTERVAL = 3600

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
BIKES_ENDPOINT_TMPL = "/v2/service/{country}/bmc-user-bikes"
