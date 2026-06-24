# BMW CloudSync — field reference

Field definitions for the BMW Motorrad CloudSync data this integration reads.

**Source:** BMW's own field dictionaries, shipped as `*_meta.csv` files inside the
**CarData / GDPR data export** you can download from your BMW account
(no sniffing or reverse-engineering required). The original CSVs are kept
alongside this file for reference:

- [`cloudsync_bikes_meta.csv`](./cloudsync_bikes_meta.csv) — bike status
- [`cloudsync_recorded_tracks_meta.csv`](./cloudsync_recorded_tracks_meta.csv) — ride history
- [`cloudsync_protocolbuffers_meta.csv`](./cloudsync_protocolbuffers_meta.csv) — the GPS track-point schema

The same field names appear in the live API responses
(`/cnrd/cloudsync/v2/bikes` and `/cnrd/cloudsync/v2/recordedTracks`), so this
doubles as documentation for the integration's parsing.

> The export is a manual, one-off snapshot — it is **not** a live feed and does
> not replace the integration's polling. It is useful for one-off analysis and
> for contributing data from other bike models.

---

## Important notes

- **Tyre pressure is in BAR, not psi.** BMW's `Unit` column labels
  `tirePressureFront`/`tirePressureRear` as "psi", but the field description says
  "in bar" and the values confirm bar (e.g. ~2.3 / ~2.5). The integration treats
  these as bar.
- **`fuelLevel` mirrors the battery on electric bikes.** On an EV, `fuelLevel`
  and `energyLevel` report the same percentage.
- **Timestamps:** `*_lastChangedAt` is in **milliseconds**; most others
  (`lastConnectedTime`, `startTimestamp`, …) are in **seconds**.
- **Distances are in metres** (`totalMileage`, `rideDistance`, `remainingRange`,
  …); the integration converts to km.

---

## Electric vs combustion (EV gating)

BMW marks several fields as electric-only. Their presence is a reliable way to
tell an EV from a combustion bike — no separate flag needed:

| Field | Meaning | Only on |
|---|---|---|
| `energyLevel` | Battery state, % | electric |
| `remainingRangeElectric` | Range on current charge, m | electric |
| `chargingTimeEstimationElectric` | Remaining charge time, min | electric |
| `chargingMode` | Only value `ChargingMode_DcHvCharging` | electric |
| `fuelLevel` | Fuel %, mirrors battery on EVs | all |
| `remainingRange` | Fuel/general range, m | all |

**Rule of thumb:** a non-null `energyLevel` (or a present `chargingMode`) means
the bike is electric. This lets a generic build gate the battery/charging
sensors on field presence rather than on a model list.

---

## `cloudsync_bikes` — bike status

| Field | Description | Type | Unit |
|---|---|---|---|
| `itemId` | Unique id, e.g. `CloudBike#…` | string | |
| `vin` | VIN (17-digit long, or 7-digit short) | string | |
| `vehicleId` / `hashedLongVin` | SHA-256 of the long VIN | string | |
| `hashedShortVin` | SHA-256 of the short VIN | string | |
| `typeKey` | Model code, e.g. `0C51` | string | |
| `vehicleType` | Numeric model id (1:1 with `typeKey`) | integer | |
| `name` | Model name, or a custom name set by the owner | string | |
| `color` | Colour code, e.g. `P0NB5` | string | |
| `energyLevel` | Battery state (electric) | integer | % |
| `fuelLevel` | Fuel level (mirrors battery on EVs) | integer | % |
| `chargingMode` | Charging mode (electric) | string | |
| `remainingRangeElectric` | Range on charge (electric) | integer | m |
| `chargingTimeEstimationElectric` | Charge time left (electric) | integer | min |
| `remainingRange` | Fuel/general range | integer | m |
| `totalMileage` | Total mileage | integer | m |
| `trip1` | Trip 1 mileage | integer | m |
| `totalConnectedDistance` | Distance ridden connected to the app | integer | m |
| `totalConnectedDuration` | Time ridden connected to the app | integer | s |
| `tirePressureFront` | Front tyre pressure (**bar**) | float | bar |
| `tirePressureRear` | Rear tyre pressure (**bar**) | float | bar |
| `nextServiceDueDate` | Next service due date | integer | unix s |
| `nextServiceRemainingDistance` | Distance to next service | integer | m |
| `lastConnectedTime` | Last Bluetooth connection | integer | unix s |
| `lastActivatedTime` | Map-activation timestamp (0 = never) | integer | unix s |
| `lastConnectedLat` / `lastConnectedLon` | Position at disconnect | float | degrees |
| `_deleted` | Item deleted flag | bool | |

---

## `cloudsync_recorded_tracks` — ride history

| Field | Description | Type | Unit |
|---|---|---|---|
| `itemId` | Unique id, e.g. `CloudRecordedTrack#…` | string | |
| `title` | Ride title | string | |
| `bikeId` | Bike that recorded the ride (= `vehicleId`) | string | |
| `isFavorite` | Marked as favourite | bool | |
| `recording` | Recording in progress | bool | |
| `startTimestamp` / `endTimestamp` | Start/end time | integer | unix s |
| `startLat` / `startLon` | Start position | float | degrees |
| `endLat` / `endLon` | End position | float | degrees |
| `rideDistance` | Ride distance | integer | m |
| `rideTime` | Riding time | integer | s |
| `speedAverageKmh` | Average speed | float | km/h |
| `speedMaxKmh` | Max speed (null on older rides) | float | km/h |
| `temperatureMaxC` / `temperatureMinC` | Outside temp range | integer | °C |
| `elevationMaxM` / `elevationMinM` | Elevation range | integer | m |
| `engineMaxRpm` | Max engine rpm | integer | rpm |
| `leanAngleLeftMax` / `leanAngleRightMax` | Max lean angle each way | float | degrees |
| `accelerationMax` / `decelerationMax` | Max accel/decel | float | g |
| `trackSegments` | Pointers to the GPS track files (protobuf, see below) | list | |
| `_deleted` | Item deleted flag | bool | |

---

## GPS track points (protobuf)

The actual GPS line for each ride lives in the gzipped protobuf files referenced
by `trackSegments`, not in the JSON above. `cloudsync_protocolbuffers_meta.csv`
documents that schema. Highlights:

- **`TrackPoint`** — `latitude`, `longitude`, `speed`, `elevation`,
  `timestampInMillis`: the raw GPS line.
- **`BikeVdsData`** — rich per-sample telemetry: real-time banking angle, gear,
  throttle, brake pressures, engine/outside temperature, per-sample tyre
  pressure, energy level/consumption, and more.

Decoding these requires fetching the segment files and parsing protobuf against
this schema — a separate effort, not currently part of the integration. The
per-ride summary fields in `cloudsync_recorded_tracks` cover everything the
integration exposes today.
