
Claude is responding
hej vill att du gör en full code review av https://github.com/perstromqvist/bmw-ce04-ha och berättar om någonting är fel elle rborde ändras? Det är ett HACS intergation för senaste version av Home Assistant

11:19

Fetched: GitHub - perstromqvist/bmw-ce04-ha
Fetched: GitHub - perstromqvist/bmw-ce04-ha
Låt mig hämta alla källfiler.


Searched the web
Searched the web
Sökningen hjälpte inte med råfilerna. Låt mig prova direkt med GitHub API.


Ran 9 commands, searched the web
Ran 9 commands, searched the web
Bra, nu har jag all kod. Låt mig göra en grundlig analys.


Ran 3 commands
Ran 3 commands
Nu har jag en komplett bild. Sammanfattar alla findings:

Jag har nu full bild av koden. Här är min code review:

Code Review — bmw-ce04-ha v1.4.0
🔴 Kritiska buggar (bryter funktionalitet)
1. async_refresh_token_if_needed existerar inte I coordinator.py rad 46 anropas self.client.async_refresh_token_if_needed(), men den metoden finns inte i api.py. Det finns bara async_refresh_token(). Detta kastar AttributeError vid varje poll-cykel — coordinatorn fungerar aldrig efter initial setup.

Lösning: antingen byta till async_refresh_token(), eller lägga till en ny metod i api.py:

python
async def async_refresh_token_if_needed(self) -> None:
    if self._token and self._token.expires_at <= datetime.now(tz=UTC):
        await self.async_refresh_token()
2. CE04Data.from_api() kallas dubbelt api.py returnerar redan [CE04Data.from_api(item) for item in items], men coordinator.py rad 93 kör sedan CE04Data.from_api(bike) igen — på ett objekt som redan är en CE04Data. Metoden förväntar sig ett råobjekt med .bike_id, .name osv., men ett CE04Data-objekt har exakt samma attribut och råkar fungera — tills BMW ändrar något. Det är en latent krasch och logiken är fel.

Koordinatorn ska bara göra result[bike.bike_id] = bike, inte parse:a om.

3. image-plattformen är registrerad men saknas i PLATFORMS image.py med CE04BikeImage-klassen finns, men const.py definierar:

python
PLATFORMS = ["sensor", "binary_sensor", "device_tracker"]
"image" saknas → image.py laddas aldrig, image-entiteter skapas aldrig.

4. Bildfilerna är .jpg men koden refererar .png www/-mappen innehåller blue.jpg, silver.jpg, white.jpg. Sensor.py rad 66 och image.py rad 43/57 bygger URL:er som f"/local/{color}.png". Bilderna hittas aldrig.

🟠 Funktionella problem (dåligt beteende)
5. Services registreras om vid varje config entry reload hass.services.async_register(...) anropas i async_setup_entry utan att kontrollera om de redan är registrerade. Om integration laddas om (t.ex. vid token-refresh) kraschar HA med en konflikt. Och vid async_unload_entry avregistreras de aldrig.

Rätt mönster:

python
if not hass.services.has_service(DOMAIN, "force_update"):
    hass.services.async_register(...)
# och i unload:
hass.services.async_remove(DOMAIN, "force_update")
6. charging-sensorn är alltid True om chargingMode-nyckeln finns

python
value_fn=lambda bike: bike.raw.get("chargingMode") is not None
Det kontrollerar om nyckeln existerar, inte om laddning pågår. BMW skickar förmodligen chargingMode: null eller "OFF" även när laddning inte sker — då triggas sensorn ändå. Bör kontrollera värdet, t.ex. bike.raw.get("chargingMode") not in (None, "OFF", "INACTIVE").

7. online-sensorn är missvisande

python
value_fn=lambda bike: bike.last_connected_time is not None
Sensorn slår till permanent så fort en anslutning skett någonsin. Det är inte "online", det är "har anslutit". Reellt online-läge är omöjligt att avgöra med polling, men det bör åtminstone heta något annat eller använda ett färskt timestamp-check.

8. Reauth-flödet är brutet async_step_reauth hoppar direkt till async_step_authorize() och skippar async_step_reauth_confirm. reauth_confirm-steget är definierat men aldrig nås från det faktiska flödet. Dessutom saknas reauth_confirm-steget i strings.json (finns i en.json men inte i master-strings-filen).

🟡 Designproblem och tekniska skulder
9. COLOR_MAP definieras på tre ställen Samma dictionary finns i const.py, helpers.py och inuti image.py som lokal variabel. helpers.map_color() returnerar "unknown" vid okänd kod, men sensor.py använder resultatet direkt som filnamn (/local/unknown.png — finns inte). image.py defaultar till "white". Inkonsistent beteende.

Lösning: ta bort COLOR_MAP från helpers.py och image.py, importera från const.py och välj ett konsekvent default-beteende.

10. CONF_POLL_INTERVAL saknas i entry.data för äldre installationer

python
poll_interval = entry.options.get(CONF_POLL_INTERVAL, entry.data[CONF_POLL_INTERVAL])
Om en användare uppgraderar från en version som inte sparade poll_interval i entry.data (t.ex. om det ändrades) ger entry.data[CONF_POLL_INTERVAL] KeyError. Använd .get() med default:

python
poll_interval = entry.options.get(CONF_POLL_INTERVAL) or entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
11. diagnostics.py exponerar fullständigt raw-data och entry.data (inkl. token)

python
return {
    "entry_data": entry.data,  # innehåller access_token, refresh_token!
    ...
    "raw": bike.raw,  # okänd mängd PII
}
entry.data innehåller token med access_token och refresh_token i klartext. Diagnostik-filer ska anonymiseras. VIN maskeras redan korrekt men tokens missas helt.

12. manifest.json saknar homeassistant (min version) hacs.json har "homeassistant": "2025.1.0" men manifest.json saknar det. HA använder manifest för att blockera inkompatibla versioner — utan det kan integrationen laddas på gamla HA-versioner.

13. Oanvänd import i diagnostics.py

python
from homeassistant.helpers.typing import ConfigType
ConfigType används ingenstans i filen.

14. import json i __init__.py är oanvänd

python
import json
Importeras men används inte i __init__.py.

🟢 Bra saker att lyfta fram
Strukturen är i grunden solid — separation av api/coordinator/entity/models är korrekt HA-mönster. PKCE-implementationen i OAuth Device Flow är korrekt. Error handling i _async_update_data med rätt UpdateFailed-wrapping och reauth-trigger är rätt approach. @dataclass(slots=True) används genomgående, vilket är bra för prestanda. SensorStateClass.TOTAL_INCREASING på odometern är korrekt.

Prioriteringsordning för fixes:

Bug #1 (AttributeError på poll) — integration fungerar inte alls
Bug #3+4 (image-plattform + .jpg/.png) — image-entiteter saknas
Bug #2 (dubbel from_api) — latent krasch
Bug #5 (services-konflikt vid reload)
Bug #11 (token i diagnostics)
Är det bättre med async refresh i coordinator eller ny metod i api?

11:25
Ny metod i api.py är bättre. Coordinator ska inte behöva förstå token-logiken — det är API-klientens ansvar att veta när den behöver refresha. Coordinator vet bara att den vill ha data, inte hur auth fungerar.

python
async def async_refresh_token_if_needed(self) -> None:
    """Refresh token only if it's expired or about to expire."""
    if not self._token:
        raise CE04AuthError("Not authenticated")
    if self._token.expires_at <= datetime.now(tz=UTC):
        await self.async_refresh_token()
Du kan också lägga in en liten margin (t.ex. 60 sekunder) för att undvika race conditions där tokenet löper ut mitt i ett API-anrop:

python
if self._token.expires_at <= datetime.now(tz=UTC) + timedelta(seconds=60):
    await self.async_refresh_token()
_ensure_token() i api.py gör faktiskt redan exakt detta — problemet är bara att coordinatorn anropar en metod som inte existerar istället för att använda _ensure_token (som dock är privat och anropas implicit av async_get_bikes ändå). Så egentligen behöver coordinatorn inte anropa refresh alls — async_get_bikes tar hand om det via _ensure_token. Det enklaste felet är att bara ta bort anropet i coordinatorn och låta API-klienten sköta sig själv.

OK, visa mig en korrekt api.py att klistra in

11:25

Re-read api.py before editing
Re-read api.py before editing
Två ändringar: _ensure_token får en 60-sekunders margin och döps om till publik async_ensure_token som coordinatorn kan anropa — plus att _parse_bikes slutar anropa CE04Data.from_api (rådatan parsas direkt). Här är hela filen:


Created a file, read a file
Created a file, read a file
Tre ändringar mot originalet:

1. _ensure_token → publik async_ensure_token med 60s margin Coordinatorn anropar nu await self.client.async_ensure_token() istället för den metod som inte existerade. Margin på 60 sekunder innebär att token refreshas proaktivt innan den faktiskt löper ut.

2. TOKEN_EXPIRY_MARGIN som modul-konstant Lätt att justera utan att gräva i metoden.

3. except-klausul i async_get_bikes fångar inte längre CE04ApiError/CE04AuthError Originalet hade en latent bugg där except Exception längst ned kunde wrappa en redan korrekt CE04AuthError i en CE04ApiError. Nu re-raisas specifika API-exceptions explicit innan den generella fångaren.

Du behöver också uppdatera coordinatorn på rad 46 — byt ut:

python
await self.client.async_refresh_token_if_needed()
mot:

python
await self.client.async_ensure_token()

Api
PY 
OK, visa mig nu en korrekt image.py med dina fixar

11:29

Re-read image.py
Re-read image.py
Tre fixes: .png → .jpg, COLOR_MAP importeras från const.py istället för lokal kopia, och image_url som property tas bort till förmån för _handle_coordinator_update så HA märker att bilden ändrats när färgkoden uppdateras.


Created a file, read a file
Created a file, read a file
Vad som ändrades:

.png → .jpg — matchar de faktiska filerna i www/.

COLOR_MAP importeras från const.py — ingen lokal kopia. Kräver att du också lägger till DEFAULT_COLOR = "white" i const.py (det saknades — du hade DEFAULT_COLOR som en implicit default i image.py men inte exporterad från const).

_resolve_image_url() istället för _update_image_url() — ren funktion som returnerar ett värde istället för att muttera state som sidoeffekt. Lättare att följa.

_handle_coordinator_update() istället för image_url property — det rätta HA-mönstret. Originalet körde _update_image_url() inne i en property-getter, vilket betyder att HA aldrig fick veta att bilden ändrats (ingen async_write_ha_state anropades). Nu uppdateras _attr_image_url när coordinatorn pushar ny data, och super()._handle_coordinator_update() skickar state-uppdateringen till HA.

async_added_to_hass borttagen — onödig, __init__ sätter redan rätt URL och _handle_coordinator_update håller den uppdaterad.

Glöm inte lägga till "image" i PLATFORMS-listan i const.py.


Image
PY 
OK, visa nu en const.py också

11:30

Created a file, read a file
Created a file, read a file
Två ändringar mot originalet:

"image" tillagt i PLATFORMS — fixar buggen där image-entiteter aldrig laddades.

DEFAULT_COLOR = "white" tillagd — exporteras nu från const.py så att image.py och eventuellt sensor.py


Const
PY 




Claude is AI and can make mistakes. Please double-check responses.
Const · PY
from __future__ import annotations
 
# ---------------------------------------------------------------------------
# Domain & Platforms
# ---------------------------------------------------------------------------
 
DOMAIN = "bmw_ce04"
LOGGER_NAME = DOMAIN
 
PLATFORMS = ["sensor", "binary_sensor", "device_tracker", "image"]
 
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
 
# Recommended HA-style bounds
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
 
# ---------------------------------------------------------------------------
# Color mapping (single source of truth)
# ---------------------------------------------------------------------------
 
COLOR_MAP: dict[str, str] = {
    "P0N3H": "white",
    "P0NB5": "blue",
    "P0N2M": "silver",
}
 
DEFAULT_COLOR = "white"
 
