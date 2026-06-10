"""Constant definitions for the APsystems Storage integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import EntityCategory

# Integration domain, must match the domain in manifest.json
DOMAIN = "apsystems_storage"

# Keys used in the configuration flow
CONF_IP = "ip"
CONF_PORT = "port"

# Default port
DEFAULT_PORT = 80

# List of endpoints to poll
GET_ENDPOINTS = [
    "devices",
    "alarms",
    "energies",
    "modes",
    "control-panels",
]

# Manufacturer name for device registry
MANUFACTURER = "APsystems"

# Device model for device registry
MODEL = "APsystems Storage"

# Keys in the devices endpoint that map to device registry fields.
# These are NOT created as sensor entities; instead they are written into the
# Home Assistant device registry so they appear on the device info card.
DEVICE_INFO_KEYS = {
    "dev_id": "serial_number",   # → Device Registry serial_number
    "type": "model",             # → Device Registry model
    "dev_ver": "sw_version",     # → Device Registry sw_version
}

# Sensor configurations with entity metadata.
#
# Design principles applied here:
#   1. Device identity fields (dev_id, type, dev_ver) are NOT listed here;
#      they are written to the device registry in async_setup_entry so that
#      Home Assistant shows them on the device info card rather than as
#      separate sensor entities.
#   2. Parameters that already have a dedicated configurable entity
#      (select / switch / number / text) are NOT duplicated as read-only
#      sensor entities.  Those platforms own the read+write lifecycle.
#      Affected fields removed:
#        modes   → data.mode        (→ select: Operating Mode)
#        modes   → data.eco         (→ switch: Eco Mode)
#        modes   → data.offgrid_on  (→ switch: Off-grid On Hold)
#        modes   → data.time_cfg    (→ text:   Time Configuration)
#        modes   → data.dod         (→ number: Depth of Discharge)
#        modes   → data.backup_charP(→ number: Backup Charge Power)
#        panels  → data.mode        (→ switch: Control Panel Mode)
#        panels  → data.MI1         (→ text:   Control Panel Configuration)
#
# Each entry defines:
#   endpoint          – API endpoint key
#   key               – dot-separated JSON path within the response
#   name              – human-readable entity name
#   device_class      – SensorDeviceClass or None
#   state_class       – SensorStateClass or None
#   entity_category   – EntityCategory or None (None → appears in Sensors)
#   native_unit       – unit of measurement or None
#   icon              – MDI icon string
#   disabled_by_default – whether the entity is hidden by default
SENSOR_CONFIGS: list[dict[str, str | None | bool]] = [

    # -------------------------------------------------------------------------
    # devices endpoint – only the rated battery capacity remains as a sensor.
    # Device ID / Type / Firmware Version are handled via the device registry
    # (see DEVICE_INFO_KEYS above and async_setup_entry in __init__.py).
    # -------------------------------------------------------------------------
    {
        "endpoint": "devices",
        "key": "data.bat_cap",
        "translation_key": "battery_capacity",
        "name": "Battery Capacity",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": None,
        "native_unit": "kWh",
        "disabled_by_default": False,
    },
    {
        "endpoint": "devices",
        "key": "data.bat_manuf",
        "translation_key": "battery_manufacturer",
        "name": "Battery Manufacturer",
        "device_class": None,
        "state_class": None,
        "entity_category": None,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "devices",
        "key": "data.bat_model",
        "translation_key": "battery_model",
        "name": "Battery Model",
        "device_class": None,
        "state_class": None,
        "entity_category": None,
        "native_unit": None,
        "disabled_by_default": False,
    },
    


    # -------------------------------------------------------------------------
    # alarms endpoint – all alarm flags; shown under Diagnostic.
    # -------------------------------------------------------------------------
    {
        "endpoint": "alarms",
        "key": "data.bat_overtemp",
        "translation_key": "battery_high_temperature",
        "name": "Battery High Temperature",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.bat_undertemp",
        "translation_key": "battery_low_temperature",
        "name": "Battery Low Temperature",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.bat_comm_err",
        "translation_key": "battery_communication_error",
        "name": "Battery Communication Error",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.bat_overvolt",
        "translation_key": "battery_overvoltage",
        "name": "Battery Overvoltage",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.bat_undervolt",
        "translation_key": "battery_undervoltage",
        "name": "Battery Undervoltage",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.bat_overcur",
        "translation_key": "battery_overcurrent",
        "name": "Battery Overcurrent",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.bat_ie",
        "translation_key": "battery_internal_error",
        "name": "Battery Internal Error",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.dev_temp",
        "translation_key": "device_temperature_protection",
        "name": "Device Temperature Protection",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.dev_sys_err",
        "translation_key": "device_system_error",
        "name": "Device System Error",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.bat_shutdown",
        "translation_key": "battery_shutdown",
        "name": "Battery Shutdown",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.grid_anomaly",
        "translation_key": "ongrid_abnormal",
        "name": "On-grid Abnormal",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.offgrid_overcur",
        "translation_key": "offgrid_overcurrent",
        "name": "Off-grid Overcurrent",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.offgrid_shortcir",
        "translation_key": "offgrid_short_circuit",
        "name": "Off-grid Short Circuit",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },
    {
        "endpoint": "alarms",
        "key": "data.bat_cal",
        "translation_key": "battery_capacity_calibration",
        "name": "Battery Capacity Calibration",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },

    # -------------------------------------------------------------------------
    # energies endpoint – real-time measurement sensors; shown under Sensors.
    # Battery Status is the only non-measurement field here; kept as Diagnostic.
    # -------------------------------------------------------------------------
    {
        "endpoint": "energies",
        "key": "data.bat_soc",
        "translation_key": "battery_soc",
        "name": "Battery SOC",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": None,
        "native_unit": "%",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.bat_temp",
        "translation_key": "battery_temperature",
        "name": "Battery Temperature",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": None,
        "native_unit": "\u00b0C",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.dev_temp",
        "translation_key": "device_temperature",
        "name": "Device Temperature",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": None,
        "native_unit": "\u00b0C",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.bat_impE",
        "translation_key": "battery_accumulated_charge_energy",
        "name": "Battery Accumulated Charge Energy",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "entity_category": None,
        "native_unit": "kWh",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.bat_expE",
        "translation_key": "battery_accumulated_discharge_energy",
        "name": "Battery Accumulated Discharge Energy",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "entity_category": None,
        "native_unit": "kWh",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.ongrid_expE",
        "translation_key": "ongrid_accumulated_output_energy",
        "name": "On-grid Accumulated Output Energy",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "entity_category": None,
        "native_unit": "kWh",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.ongrid_impE",
        "translation_key": "ongrid_accumulated_input_energy",
        "name": "On-grid Accumulated Input Energy",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "entity_category": None,
        "native_unit": "kWh",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.offgrid_expE",
        "translation_key": "offgrid_accumulated_output_energy",
        "name": "Off-grid Accumulated Output Energy",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "entity_category": None,
        "native_unit": "kWh",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.offgrid_impE",
        "translation_key": "offgrid_accumulated_input_energy",
        "name": "Off-grid Accumulated Input Energy",
        "device_class": None,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "entity_category": None,
        "native_unit": "kWh",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.bat_power",
        "translation_key": "battery_power",
        "name": "Battery Power",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": None,
        "native_unit": "W",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.ongrid_power",
        "translation_key": "ongrid_power",
        "name": "On-grid Power",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": None,
        "native_unit": "W",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.offgrid_power",
        "translation_key": "offgrid_power",
        "name": "Off-grid Power",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "entity_category": None,
        "native_unit": "W",
        "disabled_by_default": False,
    },
    {
        "endpoint": "energies",
        "key": "data.bat_status",
        "translation_key": "battery_status",
        "name": "Battery Status",
        "device_class": None,
        "state_class": None,
        "entity_category": EntityCategory.DIAGNOSTIC,
        "native_unit": None,
        "disabled_by_default": False,
    },

    # -------------------------------------------------------------------------
    # modes / control-panels endpoints
    #
    # All writable parameters from these endpoints already have dedicated
    # configurable entities (select / switch / number / text).  Duplicating
    # them here as read-only sensors would create redundant entities that
    # confuse users (see Design Principles comment above).
    #
    # Nothing is listed here; the configurable entities handle both display
    # and write-back for all modes / control-panels fields.
    # -------------------------------------------------------------------------
]
