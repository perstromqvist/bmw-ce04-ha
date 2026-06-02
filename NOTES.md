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

## Neutralization checklist (future, v2.0.0)

- Domain `bmw_ce04` → `bmw_motorrad` (breaking — requires re-add).
- Base universal sensors on `fuelLevel` / `remainingRange`; gate EV sensors on
  the EV fields being present.
- Keep the model `from_api` null-safe (already is) so missing fields just yield
  empty sensors on other models.
- Confirm field shape on a non-CE-04 model via `export_raw_data` before relying
  on any of the above for other bikes.
