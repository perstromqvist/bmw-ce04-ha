# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project aims to follow [Semantic Versioning](https://semver.org/).

<!-- Dates are approximate — adjust to your actual release dates. -->

## [1.5.4] - 2026-06-04

### Added
- `tools/dump_raw.py` and a "Contributing data" guide for sharing a (masked) raw dump without Home Assistant.

### Fixed
- README: corrected the vehicle-image setup note, the `force_update` parameters, and the diagnostics description.

## [1.5.3] — 2026-06-03

### Fixed
- Charging detection now matches BMW's actual `chargingMode` value
  (`ChargingMode_DcHvCharging`). The CE 04 AC-charges and rarely reports this
  field, so power-based detection is still more reliable for it — but the sensor
  is now correct for any model/charge type that does report it.

### Added
- `NOTES.md` — developer reference for the BMW CloudSync and CarData data models:
  field meanings, verified colour codes, and groundwork for a future
  model-neutral version.
- `tools/check_auth.py` — optional standalone script to verify your CarData
  Client ID and BMW account *outside* Home Assistant when setup won't work.

### Changed
- README: one-click "Open in HACS" button, a setup-troubleshooting note, and
  corrected image/diagnostics details.

## [1.5.2] — 2026-06-02

### Fixed
- The vehicle image now maps correctly to the bike's colour, including decal
  variants (e.g. `P0NB5-EI00257P`): the full colour code is matched first, then
  the base colour, then a generic fallback.

## [1.5.1] — 2026-06-02

### Changed
- Options now apply immediately — the integration reloads itself on save, so
  settings such as the poll interval take effect without restarting Home
  Assistant.

## [1.5.0] — 2026-06-02

### Fixed
- Reauthentication now updates the existing entry instead of aborting, so
  re-login works when a token expires.
- The `bmw_ce04.export_raw_data` service now actually returns the raw payload.
- `device_tracker` no longer crashes when the VIN is missing.
- Charging detection hardened (case-insensitive, null-safe).

### Changed
- Default poll interval is now 30 minutes (minimum 10), staying well under BMW's
  API quota. Existing installations keep their current setting until changed.
- Entities now report "unavailable" when a poll fails, instead of showing stale
  values.
- Setup asks only for your CarData Client ID; host and SSL are handled
  internally.
- The "Online" binary sensor is now "Recently connected", with a tunable time
  window.
- Clearer, numbered authorization instructions during setup.
- Diagnostics now include the full raw payload, with VIN, IDs and GPS redacted.
- The "Trip 2" sensor is disabled by default (not reported by the CE 04).
- Cleaned up the manifest; minimum HA version is sourced from `hacs.json`.

### Added
- "Last update" diagnostic timestamp sensor (stays available when polling fails,
  so you can alert on a stalled integration).
- The vehicle image falls back to a replaceable `mc_image.jpg` for unknown
  colour codes.

## [1.4.x and earlier]

Initial development releases — see the Git commit history for details.

<!-- Link references — adjust if your tags are named differently. -->
[Unreleased]: https://github.com/perstromqvist/bmw-ce04-ha/compare/v1.5.3...HEAD
[1.5.3]: https://github.com/perstromqvist/bmw-ce04-ha/compare/v1.5.2...v1.5.3
[1.5.2]: https://github.com/perstromqvist/bmw-ce04-ha/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/perstromqvist/bmw-ce04-ha/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/perstromqvist/bmw-ce04-ha/releases/tag/v1.5.0
