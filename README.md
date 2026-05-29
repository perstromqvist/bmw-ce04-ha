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

---

A custom Home Assistant integration for the **BMW Motorrad CE 04** electric scooter, using the official **BMW ConnectedRide / CarData cloud API**.

This integration is **read‑only** and does **not** send any remote commands to the scooter.

---

## 🚀 Features

This integration pulls live data from the BMW Motorrad cloud and exposes it as Home Assistant entities.

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
A dedicated sensor automatically displays the correct CE 04 image based on your scooter’s color code:

- Light White  
- Imperial Blue  
- Magellan Grey / Space Silver  

Images are served from `/local/`.

### 🧩 Home Assistant Native Features
- Full **Config Flow** setup (no YAML)
- **Reauthentication** when token expires
- **Diagnostics** support (export anonymized data)
- **Device registry** integration
- **Entity categories** for clean UI grouping

---

## 📦 Requirements

- Home Assistant (latest recommended)
- HACS installed
- A **BMW CarData Client ID**  
  → Register at: https://bmw-cardata.bmwgroup.com/customer/public/api-documentation/Id-Technical-registration_Step-1  
- A BMW Motorrad account with **ConnectedRide** enabled in the app

---

## 🛠️ Installation via HACS

1. Go to **HACS → Integrations**
2. Click the three dots → **Custom repositories**
3. Add this repository URL  
4. Choose **Integration**
5. Open **BMW Motorrad CE 04** in HACS and click **Download**
6. **Restart Home Assistant**
7. Go to **Settings → Devices & Services → Add Integration**
8. Search for **BMW CE 04**

---

## 🔐 Authentication

This integration uses the official **BMW CarData OAuth Device Code Flow**.

During setup you will:

1. Enter your CarData Client ID
2. Receive a verification URL and user code
3. Approve the device in the BMW portal
4. Return to Home Assistant and click **Submit**

If your token expires, Home Assistant will automatically trigger **Reauthentication**.

---

## 🧪 Debugging (optional)

If you create a file named:

