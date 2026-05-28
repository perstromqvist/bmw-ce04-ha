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
</p>

***

Custom Home Assistant integration for the BMW Motorrad CE 04 electric scooter, using the BMW ConnectedRide / CarData cloud API.

## What it does

Pulls data from the BMW Motorrad cloud and creates Home Assistant entities:

- **EV Battery & Charging:**
  - Battery level (%)
  - Remaining electric range (km)
  - Charging time estimation (minutes remaining when charging)
  - Battery maximum capacity / State of Health (%)
- **Odometer & Trip:**
  - Total mileage (km)
  - Trip 1 (km)
  - Trip 2 (km)
- **Tyre Pressures:**
  - Tyre pressure front and rear (bar)
- **Service & Diagnostics:**
  - Next service due date
  - Next service remaining distance (km)
  - Last connected and last activated timestamps
- **Location:**
  - Last known GPS location (device tracker)
- **Binary Sensors:**
  - Low battery, low tyre pressure (front/rear), service due soon
- **Dynamic Presentation:**
  - Dynamic vehicle image sensor (`sensor.bmw_ce04_bike_image`) that automatically renders the correct official scooter visual matching your vehicle's specific color code (`Light White`, `Imperial Blue`, or `Magellan Grey / Space Silver`).

*Read-only — no remote commands are sent to the scooter.*

## Requirements

- Home Assistant
- HACS
- A BMW CarData Client ID from the BMW CarData portal (This is the most critical part; if you don't already have a CarData Client ID, follow the instructions on https://bmw-cardata.bmwgroup.com/customer/public/api-documentation/Id-Technical-registration_Step-1 first and proceed with this integration afterwards).
- A BMW Motorrad account with ConnectedRide / cloud sync enabled in the app

## Installation via HACS

1. Go to **HACS** → **Integrations**
2. Click the three dots in the top right corner and choose **Custom repositories**
3. Paste the URL to this repository, select **Integration** as the category, and click **Add**
4. Click on the **BMW Motorrad CE 04** card, select **Download**
5. **Restart Home Assistant**
