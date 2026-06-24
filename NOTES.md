# Developer notes — BMW Motorrad CloudSync data

Working reference for this integration, distilled from BMW's official
**ConnectedRide CloudSync** data dictionary (the "download my data" export) and
from real `raw` payloads. Kept here to guide future work — especially making the
integration model-neutral (`bmw_motorrad`) instead of CE 04-specific.

## Data sources — two different channels

- **Live API** (`cpp.bmw-motorrad.com`) — what this integration polls. Returns
  the `CloudBike` object plus a few EV-computed fields. This is the only data
  the integration can use at runtime.
- **GDPR data export** (downloaded from the BMW Motorrad site) — a richer dump
  with extra metadata and *other categories* (`CloudRecordedTrack`, `BikeVdsData`)
  that are **not** available via the live API. Useful for understanding field
  meanings, not for runtime features.

## CloudBike field reference

Fields returned for a bike, per BMW's data dictionary.

> For BMW's **complete, official** field definitions (bikes, recorded tracks, and
> the protobuf GPS schema), see [`docs/cloudsync_fields.md`](custom_components/bmw_ce04/docs/cloudsync_fields.md)
> and the original `*_meta.csv` dictionaries from the CarData export alongside it.
> The table below is the working subset this integration uses.

| Field | Type | Unit | Meaning |
|-------|------|------|---------|
| `itemId` | string | — | Unique random ID for the bike object (`CloudBike#<uuid>`). Account-linked. |
| `vin` | string | — | VIN (17-digit long or 7-digit short). |
| `vehicleId`, `hashedLongVin`, `hashedShortVin` | string | — | SHA256 hashes of the VIN. |
| `typeKey` | string | — | **Bike model identifier code** (e.g. `0C51` = CE 04). The canonical model key. |
| `vehicleType` | integer | — | Numeric type ID with a **1:1 relationship to `typeKey`** — redundant. |
| `name` | string | — | **User-editable** in the app; defaults to the model name. Not a stable identifier. |
| `color` | string | — | **App-selected** colour code (e.g. `P0NB5`). Not VIN-locked; changes when the user changes it in the app. |
| `fuelLevel` | integer | % | **Generic** fuel/charge level. On a BEV it mirrors the battery %. |
| `energyLevel` | integer | % | **EV-specific** battery state of charge. |
| `remainingRange` | integer | metres | **Generic** remaining range (fuel). On the CE 04 this carries the EV range. |
| `remainingRangeElectric` | integer | metres | **EV-specific** remaining range. Often `null` on the CE 04. |
| `chargingMode` | string | — | Charging mode. **Only documented value: `ChargingMode_DcHvCharging`** (DC HV). Usually `null` for AC-charging bikes like the CE 04. |
| `chargingTimeEstimationElectric` | integer | minutes | Remaining charging time reported by the bike (when charging). |
| `tirePressureFront` / `tirePressureRear` | float | **bar** | Tyre pressure. (Dictionary's unit column says "psi" but the description says bar; real values confirm **bar** — do not convert.) |
| `totalMileage` | integer | metres | Odometer. |
| `trip1` | integer | metres | Trip 1. (`trip2` is not sent for the CE 04.) |
| `nextServiceDueDate` | integer | unix s | Next service due date. |
| `nextServiceRemainingDistance` | integer | metres | Distance until next service. |
| `lastConnectedTime` | integer | unix s | Last **Bluetooth** connection between phone and bike. |
| `lastConnectedLat` / `lastConnectedLon` | float | degrees | Position when the bike was **disconnected** from the app — i.e. "last parked", not live GPS. |
| `lastActivatedTime` | integer | unix s | When the **map** was activated for the next 6-month interval (not generic "last active"). |
| `totalConnectedDistance` | integer | metres | Total distance ridden while connected to the app. |
| `totalConnectedDuration` | integer | seconds | Total time ridden while connected to the app. |
| `_version` | integer | — | Record version; starts at 1, +1 per update (+2 on version conflict). |
| `_lastChangedAt` | integer | unix ms | Last modification time of the record. **Export only — not in the live API.** |
| `_deleted` | bool | — | `true` when the item was deleted (sync tombstone). Integration skips these. |
| `__typename` | string | — | Always `CloudBike`. |

Export-only metadata not returned by the live API: `itemCreatedTimestamp`,
`_lastChangedAt`, `userId`, `userId#ItemType`.

## Key insights

- **Generic vs EV fields.** `fuelLevel` and `remainingRange` are the *universal*
  fields (present for all bikes); `energyLevel`, `remainingRangeElectric`,
  `chargingMode`, `chargingTimeEstimationElectric` are EV-specific. **For a
  neutral integration, key sensors off `fuelLevel`/`remainingRange`** and treat
  the EV fields as "present only on electric models".
- **`chargingMode`.** Only ever `ChargingMode_DcHvCharging`. The CE 04 AC-charges,
  so it's usually `null` for it — power-based charge detection (e.g. a smart plug)
  is more reliable. The charging binary sensor now matches the real value.
- **`typeKey` is the model code**, `vehicleType` is redundant (1:1). No public
  lookup table — build one empirically from dumps (`typeKey`/`vehicleType` → model).
- **`name` and `color` are app-controlled** (user-editable, change instantly).
  Stable identifiers are `vin`, `typeKey`, `vehicleId`.
- **Tyre pressure is in bar** despite the doc's "psi" unit column.
- **`lastConnectedLat/Lon` is the last *disconnect* position**, not live tracking.

## Verified CE 04 colour codes

App offers four choices; `color` reflects the app selection.

| Code | Colour |
|------|--------|
| `P0NB5` | White |
| `P0N2T` | Blue |
| `P0N3L` | Silver / grey |
| `P0NB5-EI00257P` | White with decal package (base colour + `-` suffix) |

Decal variants append a `-<code>` suffix to the base colour, so image lookup
matches the full code first, then the base colour before the dash.

## Other export categories (not in the live API)

- **`CloudRecordedTrack`** — recorded rides: `title`, `isFavorite`, `recording`,
  `bikeId`, `startTimestamp`, `startLat`/`startLon`, etc.
- **`BikeVdsData` (protocol buffers)** — per-point telemetry: timestamp,
  map-matched + raw GPS, elevation, heading, speed, accuracy.

Both are rich but only present in the data export. They would only become usable
if BMW exposes corresponding API endpoints (not currently used here).

## CarData telematics model (streaming API — a different channel)

There are **two** BMW data channels, and they use different schemas:

1. **ConnectedRide CloudSync (`CloudBike`)** — phone-synced, flat camelCase fields.
   This is what the integration polls (`cpp.bmw-motorrad.com`) and what `raw`
   contains. Available for SIM-less bikes like the CE 04.
2. **CarData telematics** — `vehicle.*` dotted descriptors, **streamed by the
   vehicle over its built-in SIM/modem** to BMW and exposed via the CarData API.
   Documented in BMW's "Customer Telematics Data Catalogue". The CE 04 has **no
   SIM**, so it does not produce this — which is why the CarData portal shows a
   reduced menu for it. The first catalogue field is literally `vehicle.sim.status`.

The integration uses CarData only for **OAuth/identity**; the data comes from
CloudBike. The richer telematics set below requires a modem-equipped bike and a
different (CarData REST/streaming) data path.

### CloudBike (`raw`) → CarData telematics descriptor

| `raw` field | CarData descriptor |
|---|---|
| `totalMileage` | `vehicle.vehicle.travelledDistance` |
| `energyLevel` | `vehicle.powertrain.electric.battery.stateOfCharge.displayed` (0–100 %) |
| `remainingRange` / `remainingRangeElectric` | `vehicle.drivetrain.electricEngine.remainingElectricRange` (0–1000 km) |
| `chargingMode` | `vehicle.drivetrain.electricEngine.charging.status` |
| `chargingTimeEstimationElectric` | `vehicle.drivetrain.electricEngine.charging.remainingTimeSme` (0–65534 min) |
| `tirePressureFront` / `tirePressureRear` | `vehicle.chassis.axle.row1`/`row2`.`wheel.center.tire.pressure` (**kPa** here, not bar) |
| `trip1` / `trip2` | `vehicle.tripMeterReading1` / `2` |
| `nextServiceDueDate` | `vehicle.status.conditionBasedServices`, `vehicle.status.lastService.timestamp`/`mileage` |
| `color` / decals | likely `vehicle.extras.optionalEquipment.code` |
| `vin` | `vehicle.vehicleIdentification.basicVehicleData` |
| `lastConnectedLat`/`Lon` | `vehicle.cabin.infotainment.navigation.currentLocation.latitude`/`longitude` (telematics is **live**; CloudBike is last-disconnect) |

### In the telematics catalogue but NOT in CloudBike `raw`

- **12 V low-voltage battery SOC** (`vehicle.electricalSystem.battery.stateOfCharge`) and battery guard (`…batteryManagement.statusBatteryGuard`: `NO_WARNING`/`WARNING`/`ALARM`).
- Ignition + engine state (`…engine.isIgnitionOn` / `isActive`).
- **Live GPS with heading and altitude** (`…currentLocation.heading`/`altitude`).
- Average consumption, check-control messages, detailed Condition Based Services, trip *duration*, per-tyre low-pressure flags (`…tire.pressureLow`).
- **`vehicle.look.image`** — a BMW-provided vehicle image (could replace the manual colour→image mapping).
- SIM status, ConnectedDrive contract list, preferred service partner.

### CarData probe result (confirmed, 2026-06)

Tested the CarData REST API with a valid token (scope `cardata:api:read`):

- `GET /customers/vehicles/mappings` → **200**, but lists only the **car** (an
  i3, `WBY…` VIN). The CE 04 is **not present** — it is not a CarData vehicle.
- `GET /customers/vehicles/{ce04_vin}/basicData` → **403 CU-104** ("no permission
  / not telematics-capable / not mapped").
- `telematicData` needs a container id (got CU-400); `image` needs `Accept:
  image/png` — both moot since the VIN is gated anyway.

**Conclusion:** CarData is **car-only** here. The CE 04 lives solely in the
Motorrad ConnectedRide / CloudSync world (`cpp.bmw-motorrad.com`). CloudBike is
the only data source for it, and `vehicle.look.image` is unavailable — so the
manual colour→image mapping is the correct solution, not a stopgap. For
**modem-equipped** models the CarData API may still be a richer source, but that
is a separate (car-style) integration path.

### Client ID creation — motorcycle-only owners (confirmed, 2026-06)

Creating a CarData Client ID requires a CarData-capable vehicle on the account.
Two owner reports (mine + a Belgian CE 04 owner) showed the Motorrad portal's
CarData tab offers only the GDPR data download, not client creation, for a
motorcycle-only account. **BMW Motorrad support then confirmed**: for the CE 04,
based on the type/model of the telematics module installed on the bike,
displaying the Client ID is not possible. So this is a telematics-module
(hardware) limit — not a mapping or second-owner issue.

Consequence: a CE 04 owner with no other BMW cannot create a Client ID and
therefore cannot use this integration. They need another CarData-capable BMW
(typically a car) on the same account. Other Motorrad models may have different
telematics modules and could behave differently — unconfirmed.

This also closes the client_id investigation. App-traffic sniffing surfaced only
device/installation IDs (push `clientId`, `X-Client-ID`) and an API-gateway key
(`x-cd-apigw-key`) — none are OAuth client IDs. The web portal's OAuth client
(`b1dd73b8…`, `authorization_code` flow) is **not** device-code-enabled
("invalid client"). Even a recovered app client_id would hit the same
telematics-module gate. Dead end, by design — pursue model-neutral support
instead.

## Neutralization checklist (future, v2.0.0)

- Domain `bmw_ce04` → `bmw_motorrad` (breaking — requires re-add).
- Base universal sensors on `fuelLevel` / `remainingRange`; gate EV sensors on
  the EV fields being present.
- Keep the model `from_api` null-safe (already is) so missing fields just yield
  empty sensors on other models.
- Confirm field shape on a non-CE-04 model via `export_raw_data` before relying
  on any of the above for other bikes.
- For modem-equipped models, consider the CarData telematics API (`vehicle.*`)
  as a richer alternative/supplement to CloudBike (see section above).
