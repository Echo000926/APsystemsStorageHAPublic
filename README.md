# APsystems Storage System (LAKE) Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Maintenance](https://img.shields.io/maintenance/yes/2026)]()

<img src="https://github.com/HAEdwin/homeassistant-apsystems_ecu_reader/blob/main/apsystemslogo.png?raw=true" width="3%"> **APsystems Storage**

> ⚠️ **Notice**: This integration is exclusively designed for **APsystems Storage Systems** (e.g., LAKE series).
> If you are using a PV microinverter system (ECU-B/R/C), please use the [APsystems ECU Reader](https://github.com/HAEdwin/homeassistant-apsystems_ecu_reader).
> If you are using an EZ1 microinverter, please use the official Home Assistant [APsystems](https://www.home-assistant.io/integrations/apsystems/) integration.

## Overview

APsystems Storage is a custom Home Assistant integration designed for local communication with APsystems storage devices (LAKE series). It enables real-time monitoring and configuration management via the device's local HTTP API, eliminating any dependency on cloud services.

### Key Features

- 📡 **Pure Local Control**: Communicates directly with the device over the LAN IP, ensuring fast and stable response times.
- 🔋 **Comprehensive Energy Monitoring**: Provides real-time data on battery SOC, temperature, charge/discharge power, cumulative energy throughput, and on-grid/off-grid power.
- ⚙️ **Advanced Configuration Management**: Allows direct modification of operating modes, power limits, Depth of Discharge (DoD), and backup charging power within Home Assistant.
- 🕒 **Time-of-Use Strategy Configuration**: Offers JSON-formatted text entities for advanced users to define complex charge/discharge scheduling strategies.
- 🛡️ **Complete Diagnostic Alerts**: Integrates over 15 status alert sensors, including battery over/under-temperature, over/under-voltage, overcurrent, communication errors, and system faults.
- ✅ **Batch Confirmation Mechanism**: Utilizes a "local staging + manual confirmation" design to prevent accidental changes; all configuration modifications are only written to the device after clicking the confirm button.
- 🔄 **Optimistic Updates**: Instantly updates the UI state and automatically refreshes device data upon successful configuration delivery, providing a seamless user experience.

## Supported Devices

| Device Type | Model Examples | Notes |
| :--- | :--- | :--- |
| All-in-One ESS | LAKE Series | ✅ Fully Supported |
| PV Microinverter ECU | ECU-B / ECU-R / ECU-C | ❌ Not Supported (Please use ECU Reader) |
| EZ1 Microinverter | EZ1-M | ❌ Not Supported (Please use Official Integration) |

## Prerequisites

- HACS must be installed in your Home Assistant instance.
- The energy storage device must be connected to the local network and assigned a **static IP address**.
- Home Assistant must have network access to the device's HTTP port (default: 80).
- Ensure no other automations or integrations are frequently occupying the device's communication interface.

## Installation

### Installation via HACS

1. Navigate to HACS → Integrations → Click the three-dot menu in the top right corner → Custom repositories.
2. Add the GitHub repository URL for this integration.
3. Search for "APsystems Storage" and download it.
4. Restart Home Assistant.
5. Go to **Settings** → **Devices & Services** → **+ Add Integration** → Search for "APsystems Storage".

## Configuration Options

### Initial Setup

When adding the integration, you will need to provide the following information:

| Parameter | Description | Default Value |
| :--- | :--- | :--- |
| IP Address | The LAN IP address of the energy storage device | - |
| Port | The HTTP API port of the device | 80 |

> 💡 The integration will automatically test the connection before creation. If the connection fails, please verify the IP address, port, and overall network connectivity.

### Reconfiguration

You can modify the IP address and port settings without deleting the integration. Navigate to the integration page → Click the three-dot menu → Select Reconfigure.

## Entity Reference

This integration provides the following entity types, categorized into **Monitoring** and **Configuration**:

### 📊 Monitoring Sensors

| Entity Name | Unit | Description |
| :--- | :--- | :--- |
| Battery SOC | % | Remaining battery state of charge |
| Battery Power | W | Real-time battery charge/discharge power |
| Battery Temperature | °C | Battery temperature |
| Device Temperature | °C | Internal device temperature |
| On-grid Power | W | Real-time on-grid side power |
| Off-grid Power | W | Real-time off-grid side power |
| Battery Accumulated Charge Energy | kWh | Cumulative battery charging energy |
| Battery Accumulated Discharge Energy | kWh | Cumulative battery discharging energy |
| On-grid Accumulated Output/Input Energy | kWh | Cumulative on-grid export/import energy |
| Off-grid Accumulated Output/Input Energy | kWh | Cumulative off-grid export/import energy |
| Battery Capacity | kWh | Rated battery capacity |
| Battery Manufacturer / Model | - | Battery manufacturer and model information |
| Battery Status | - | Current battery operating status |

### 🔧 Configuration Entities

> ⚠️ **Important Notice**: All modifications to configuration entities are **locally staged**. A `*` marker will appear next to the entity name in the UI. Changes are only written to the physical device after clicking the corresponding **Confirm** button.

#### Switches

| Entity | Description |
| :--- | :--- |
| Eco Mode | Toggle for energy-saving mode |
| Off-grid On Hold | Toggle to maintain off-grid output |
| Control Panel Mode | Toggle for control panel mode |

#### Selectors

| Entity | Options | Description |
| :--- | :--- | :--- |
| Operating Mode | AI Mode / Self Consumption / Time of Use / Backup | System operating mode selection |
| Power Limit | 800W / 2500W | Maximum power limit setting |

#### Numbers

| Entity | Range | Unit | Description |
| :--- | :--- | :--- | :--- |
| Depth of Discharge | 15 - 100 | % | Depth of discharge (DoD) setting |
| Backup Charge Power | 0 - 2500 | W | Charging power limit in backup mode |

#### Text Inputs

| Entity | Format | Description |
| :--- | :--- | :--- |
| Time Configuration | JSON Array | Time-of-use scheduling strategy for operating modes |
| Control Panel Configuration | JSON Object | Scheduling strategy for control panel settings |

#### Buttons

| Entity | Description |
| :--- | :--- |
| Confirm Modes Settings | Batch-writes all staged mode-related configurations to the device |
| Confirm Control Panels Settings | Batch-writes all staged control panel configurations to the device |

### 🔔 Diagnostic Alerts

The integration exposes comprehensive device alert states, including: battery over/under-temperature, over/under-voltage, overcurrent, communication errors, internal faults, device thermal protection, system errors, battery shutdown, on-grid anomalies, off-grid overcurrent/short circuit, and battery capacity calibration. These entities are classified under the Diagnostic category by default.


The `/alarms` endpoint returns device status flags as string values. `"0"` indicates normal status, while `"1"` indicates an active alarm or abnormal condition. All fields listed below are exposed as diagnostic binary sensors in Home Assistant.

| Entity | Description |
| :--- | :--- | :--- |
| Battery High Temperature Alarm | Battery temperature exceeds safe upper limit |
| Battery Low Temperature Alarm | Battery temperature falls below safe lower limit |
| Battery Communication Error | Communication failure between device and BMS |
| Battery Overvoltage Alarm | Battery voltage exceeds maximum threshold |
| Battery Undervoltage Alarm | Battery voltage drops below minimum threshold |
| Battery Overcurrent Alarm | Battery charge/discharge current exceeds safe limit |
| Battery Internal Error | Internal fault detected within the battery pack |
| Device Temperature Protection | Inverter/PCS internal temperature protection triggered |
| Device System Error | General system-level fault on the storage device |
| Battery Shutdown Alarm | Battery has entered shutdown state |
| Grid Abnormal Alarm | On-grid side voltage/frequency anomaly detected |
| Off-grid Overcurrent Alarm | Off-grid side output current exceeds safe limit |
| Off-grid Short Circuit Alarm | Short circuit detected on the off-grid output side |
| Battery Capacity Calibration | Battery capacity calibration in progress or completed |

> 💡 **Note**: All alarm entities are classified under the **Diagnostic** category by default and are disabled in dashboards unless explicitly enabled by the user. Each entity reports `On` when the corresponding API field equals `"1"` and `Off` when it equals `"0"`.

## How It Works

```text
┌─────────────┐     HTTP GET      ┌──────────────────┐
│             │ ◄──────────────── │                  │
│  Home       │                   │  APsystems       │
│  Assistant  │     HTTP POST     │  Storage Device  │
│             │ ────────────────► │  (LAKE)       │
└─────────────┘   (Confirm Only)  └──────────────────┘
```


### This integration employs a three-stage architecture — **"Local Staging + Batch Confirmation + Optimistic Updates"** — to balance configuration safety with an optimal user experience:

1.  **Data Collection**: The Coordinator periodically polls five endpoints: `/devices`, `/alarms`, `/energies`, `/modes`, and `/control-panels`.
2.  **Local Staging**: When a user modifies any configuration via the UI, changes are stored exclusively in memory. Affected entities display a `*` suffix to indicate a pending change. No commands are sent to the device at this stage.
3.  **Batch Submission**: Upon clicking a Confirm button, the integration aggregates all staged parameters into a unified payload and transmits it to the device via a single HTTP POST request.
4.  **Optimistic Update**: After successful submission, the Coordinator cache is updated immediately, all staging markers are cleared, and an instant refresh is triggered to synchronize the UI with the actual device state.

💡 This design significantly reduces API call frequency (avoiding per-parameter requests), enhances communication stability, and provides clear operational feedback.

## Troubleshooting

| Symptom | Possible Causes | Solutions |
| :--- | :--- | :--- |
| Unable to connect to device | • Incorrect IP address or non-standard port<br>• HTTP API not enabled on device<br>• Firewall/router blocking traffic | 1. Run `ping <device_IP>` from the HA host<br>2. Access `http://<device_IP>` in a browser to verify web interface availability<br>3. Navigate to Device Web UI → Settings → Network → Ensure "HTTP Service" is enabled |
| Configuration write failure | • Malformed JSON (especially in Time Configuration)<br>• Device busy processing other requests | 1. Validate Text entity content using JSONLint<br>2. Wait 30 seconds and retry |
