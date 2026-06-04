# BMW Motorrad CE 04 — Home Assistant Integration

<p align="center">
  <a href="https://github.com/hacs/integration">
    <img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS Custom">
  </a>
  <a href="https://github.com/perstromqvist/bmw-ce04-ha/releases">
    <img src="https://img.shields.io/github/v/release/perstromqvist/bmw-ce04-ha?style=for-the-badge&color=blue" alt="Latest Release">
  </a>
  <a href="https://github.com/perstromqvist/bmw-ce04-ha/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License MIT">
  </a>
  <a href="https://www.home-assistant.io">
    <img src="https://img.shields.io/badge/Home--Assistant-Compatible-blueviolet.svg?style=for-the-badge&logo=home-assistant" alt="Home Assistant">
  </a>
  <a href="https://claude.ai">
    <img src="https://img.shields.io/badge/Code%20reviewed%20with-Claude-D97757?style=for-the-badge&logo=claude&logoColor=fff" alt="Code reviewed with Claude">
  </a>
</p>

---

A custom Home Assistant integration for the **BMW Motorrad CE 04** electric scooter, using the official **BMW ConnectedRide / CarData cloud API**.

This integration is **read‑only** and does **not** send any remote commands to the scooter.

> [!IMPORTANT]
> **Unofficial integration.** This project is independent and is **not** affiliated with, endorsed by, or sponsored by BMW. *BMW*, *BMW Motorrad*, the *BMW logo*, and *CE 04* are trademarks of Bayerische Motoren Werke AG (BMW AG), used here solely for identification purposes.

---

## 🚀 Features

This integration pulls the latest data from the BMW Motorrad cloud and exposes it as Home Assistant entities.

### 🔋 EV Battery & Charging
- Battery level (%)
- Remaining electric range (km)
- Charging time estimation (minutes)
- Battery maximum capacity / State of Health (%)
- Charging status (binary sensor)

### 🛣️ Odometer & Trips
- Total mileage (km)
- Trip 1 (km)
- Trip 2 (km)

### 🛞 Tyre Pressures
- Front tyre pressure (bar)
- Rear tyre pressure (bar)
- Low‑pressure alerts (binary sensors)

### 🛠️ Service & Diagnostics
- Next service due date
- Remaining distance until service
- Service due soon / overdue (binary sensors)
- Last connected timestamp
- Last activated timestamp
- Battery degradation indicator

### 📍 Location Tracking
- Last known GPS location (device tracker)

### 🎨 Dynamic Vehicle Image
A dedicated image entity automatically displays the correct CE 04 image based on your scooter's color code:

- Light White
- Imperial Blue
- Magellan Grey / Space Silver

Images ship with the integration and are served automatically — there is **nothing to copy** into `config/www/`.

Note: The name of the image refers to the color code of your bike. If no match is found, the **generic** image mc_image.jpg is served as a fallback.

### 🧩 Home Assistant Native Features
- Full **Config Flow** setup (no YAML)
- **Reauthentication** when token expires
- **Diagnostics** support (export anonymized data)
- **Device registry** integration
- **Entity categories** for clean UI grouping

---

## 📦 Requirements

- Home Assistant 2026.1.0 or newer
- HACS installed
- A **BMW CarData Client ID**
  - Register at: https://bmw-cardata.bmwgroup.com/customer/public/api-documentation/Id-Technical-registration_Step-1  
- A **BMW Motorrad account**
  - Register at: https://www.bmw-motorrad.com/en/home.html
- The **BMW Motorrad Connected** app. Download from:
  - https://apps.apple.com/us/app/bmw-motorrad-connected/id1250173746 or
  - https://play.google.com/store/apps/details?id=com.bmw.ConnectedRide

---

## 🛠️ Installation via HACS

**One click** — open HACS with this repository pre-filled:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=perstromqvist&repository=bmw-ce04-ha&category=integration)

Then click **Download** and restart Home Assistant. Or add it manually:

1. Go to **HACS → Integrations**
2. Click the three dots → **Custom repositories**
3. Add this repository URL  
4. Choose **Integration**
5. Open **BMW Motorrad CE 04** in HACS and click **Download**
6. **Restart Home Assistant**
7. Go to **Settings → Devices & Services → Add Integration**
8. Search for **BMW Motorrad CE 04**

---

## 🔐 Authentication

This integration uses the official **BMW CarData OAuth Device Code Flow**.

During setup you will:

1. Enter your CarData Client ID
2. Receive a verification URL and user code
3. Approve the device in the BMW portal
4. Return to Home Assistant and click **Submit**

If your token expires, Home Assistant will automatically trigger **Reauthentication**.

> **Setup not working?** To check whether the problem is your Client ID / BMW account or Home Assistant, run the standalone [`check_auth.py`](custom_components/bmw_ce04/tools/check_auth.py) script (it's also already in your install at `config/custom_components/bmw_ce04/tools/`). It does the same device-code login and bike fetch *outside* Home Assistant — if it lists your bike, your Client ID works and the issue is on the HA side; if it fails there, it's on the BMW side (Client ID, API subscription, or vehicle mapping).

---

## 🧪 Debugging (optional)

The integration supports opt-in raw data dumping for troubleshooting. It is **disabled by default** and only activates when a trigger file is present — no data is written unless you explicitly enable it.

### Enable debug dump

Create an empty trigger file in your Home Assistant config directory:

```
config/bmw_ce04_raw_debug.json
```

Once this file exists, the coordinator will overwrite it with the latest raw API response on every poll cycle. The file contains the full `CE04Data` structure for each bike as a JSON array.

### Disable debug dump

Delete or remove the trigger file. The coordinator will stop writing on the next poll.

You can also use the built-in service to delete it from the HA UI:

**Developer Tools → Services → `bmw_ce04.clear_debug_dump`**

---

## 🔧 Services

The integration registers the following services under the `bmw_ce04` domain:

### `bmw_ce04.force_update`
Forces an immediate data refresh from the BMW cloud, bypassing the normal poll interval. Refreshes all bikes.

### `bmw_ce04.export_raw_data`
Returns the raw `CE04Data` payload currently held by the coordinator. Useful for inspecting what the API returns without enabling file dumping.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bike_id` | string | No | If provided, returns raw data for that specific bike only |

### `bmw_ce04.clear_debug_dump`
Deletes the `bmw_ce04_raw_debug.json` trigger file if it exists, effectively disabling debug dumping.

---

## 🩺 Diagnostics

Navigate to **Settings → Devices & Services → BMW Motorrad CE 04 → Download diagnostics** to export an anonymized diagnostic report.

The report includes configuration (with the token and client ID redacted), a readable summary, and the **complete raw API payload**. Sensitive fields — VIN, vehicle/account IDs and GPS coordinates — are redacted, so the report is safe to share.

---

## 🤝 Contributing data

Support for more BMW Motorrad models depends on seeing real data from them. If you'd like to help — **no Home Assistant or HACS required** — you can run a small standalone script that fetches and saves your bike's raw data:

1. Download [`dump_raw.py`](custom_components/bmw_ce04/tools/dump_raw.py).
2. Add your CarData Client ID at the top.
3. Run `python3 dump_raw.py` (Python 3.8+; on HA OS, run `apk add python3` first).
4. Log in via the printed URL and approve.

The output is **masked by default** — VIN, ID hashes, GPS and the bike name are redacted, so it's safe to share — and is saved to `bmw_motorrad_dump.json`. Please mention your **model** and **market/region** when sharing it, since available fields and units vary by both.

---

## 📄 License

MIT — see [LICENSE](LICENSE).

This is an independent, community project and is not affiliated with or endorsed by BMW AG. All BMW trademarks and the BMW logo remain the property of Bayerische Motoren Werke AG and are used here for identification purposes only.
