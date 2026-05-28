from __future__ import annotations

DOMAIN = "bmw_ce04"
PLATFORMS = ["sensor", "binary_sensor", "device_tracker", "image"]

CONF_CLIENT_ID = "client_id"
CONF_COUNTRY = "country"
CONF_API_HOST = "api_host"
CONF_AUTH_HOST = "auth_host"
CONF_POLL_INTERVAL = "poll_interval"
CONF_VERIFY_SSL = "verify_ssl"

DEFAULT_API_HOST = "https://cpp.bmw-motorrad.com"
DEFAULT_AUTH_HOST = "https://customer.bmwgroup.com"
DEFAULT_COUNTRY = "sv-SE"  # Swedish default
DEFAULT_POLL_INTERVAL = 300

ATTR_BIKE_ID = "bike_id"
ATTR_RAW = "raw"

# BMW CarData / Motorrad API endpoints
DEVICE_CODE_ENDPOINT = "/gcdm/oauth/device/code"
TOKEN_ENDPOINT = "/gcdm/oauth/token"
BIKES_ENDPOINT_TMPL = "/v2/service/{country}/bmc-user-bikes"
