# BMW CE 04 — Home Assistant Integration

Custom Home Assistant integration for the BMW CE 04 electric scooter, using the BMW CarData cloud API.

## What it does

Pulls data from the BMW Motorrad cloud and creates Home Assistant entities:

- Battery level (%)
- Remaining electric range (km)
- Total mileage (km)
- Trip 1 (km)
- Tyre pressure front and rear (bar)
- Next service date and remaining distance
- Last connected and last activated timestamps
- Last known GPS location (device tracker)
- Binary sensors: low battery, low tyre pressure (front/rear), service due soon

Read-only — no commands are sent to the scooter.

## Requirements

- Home Assistant
- HACS or manual install
- A BMW CarData client ID from the BMW CarData portal ([https://bmw-cardata.bmwgroup.com/customer/public/home])
- A BMW Motorrad account with ConnectedRide / cloud data enabled

## Installation via HACS

1. Add this repository as a custom repository in HACS
2. Type: Integration
3. Install and restart Home Assistant

## Manual installation

Copy the `custom_components/bmw_ce04` folder to your HA config:

```
/config/custom_components/bmw_ce04/
```

Restart Home Assistant.

## Configuration

Settings → Devices & Services → Add Integration → search **BMW CE 04**

Fill in:

- **BMW CarData Client ID** — from the BMW CarData portal
- **Country code** — e.g. `en-EN`
- **Motorrad API host** — default `https://cpp.bmw-motorrad.com`
- **BMW CarData auth host** — default `https://customer.bmwgroup.com`
- **Poll interval** — default `300` seconds
- **Verify SSL** — leave enabled

You will then be prompted to open a BMW verification URL and approve the device. After approval, click Submit.

## Credits
Authentication and API structure based on [Memphius/Motorrad_hassio](https://github.com/Memphius/Motorrad_hassio), adapted for the CE 04 electric scooter.

## Disclaimer
Not affiliated with BMW or BMW Motorrad. Use at your own risk.
