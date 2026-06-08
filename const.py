"""Constant definitions."""

# Integration domain, must match the domain in manifest.json
DOMAIN = "APsystemsStorage"

# Keys used in the configuration flow
CONF_IP = "ip"
CONF_PORT = "port"

# Default port
DEFAULT_PORT = 80

# List of endpoints to poll
# The key here will be used as the unique ID suffix for the sensor
GET_ENDPOINTS = [
    "devices",
    "alarms",
    "energies",
    "modes",
    "control-panels"
]


SENSOR_CONFIGS = [
    {"endpoint": "devices", "key": "data.dev_id", "name": "device_id"},
    {"endpoint": "devices", "key": "data.type", "name": "device_type"},
    {"endpoint": "devices", "key": "data.dev_ver", "name": "device_version"},
    {"endpoint": "devices", "key": "data.bat_cap", "name": "battery_capacity"},

    {"endpoint": "alarms", "key": "data.bat_overtemp", "name": "battery_high_temperature"},
    {"endpoint": "alarms", "key": "data.bat_undertemp", "name": "battery_low_temperature"},
    {"endpoint": "alarms", "key": "data.bat_comm_err", "name": "battery_communication_error"},
    {"endpoint": "alarms", "key": "data.bat_overvolt", "name": "battery_overvoltage"},
    {"endpoint": "alarms", "key": "data.bat_undervolt", "name": "battery_undervoltage"},
    {"endpoint": "alarms", "key": "data.bat_overcur", "name": "battery_overcurrent"},
    {"endpoint": "alarms", "key": "data.bat_ie", "name": "battery_internal_error"},
    {"endpoint": "alarms", "key": "data.dev_temp", "name": "device_temperature_protection"},
    {"endpoint": "alarms", "key": "data.dev_sys_err", "name": "device_system_error"},
    {"endpoint": "alarms", "key": "data.bat_shutdown", "name": "battery_shutdown"},
    {"endpoint": "alarms", "key": "data.grid_anomaly", "name": "ongrid_abnormal"},
    {"endpoint": "alarms", "key": "data.offgrid_overcur", "name": "offgrid_overcurrent"},
    {"endpoint": "alarms", "key": "data.offgrid_shortcir", "name": "offgrid_short_circuit"},
    {"endpoint": "alarms", "key": "data.bat_cal", "name": "battery_capacity_calibration"},

    {"endpoint": "energies", "key": "data.bat_soc", "name": "battery_soc"},
    {"endpoint": "energies", "key": "data.bat_temp", "name": "battery_temperature"},
    {"endpoint": "energies", "key": "data.dev_temp", "name": "device_temperature"},
    {"endpoint": "energies", "key": "data.bat_impE", "name": "battery_accumulated_charge_energy"},
    {"endpoint": "energies", "key": "data.bat_expE", "name": "battery_accumulated_discharge_energy"},
    {"endpoint": "energies", "key": "data.ongrid_expE", "name": "ongrid_accumulated_output_energy"},
    {"endpoint": "energies", "key": "data.ongrid_impE", "name": "ongrid_accumulated_input_energy"},
    {"endpoint": "energies", "key": "data.offgrid_expE", "name": "offgrid_accumulated_output_energy"},
    {"endpoint": "energies", "key": "data.offgrid_impE", "name": "offgrid_accumulated_input_energy"},
    {"endpoint": "energies", "key": "data.bat_power", "name": "battery_power"},
    {"endpoint": "energies", "key": "data.ongrid_power", "name": "ongrid_power"},
    {"endpoint": "energies", "key": "data.offgrid_power", "name": "offgrid_power"},
    {"endpoint": "energies", "key": "data.bat_status", "name": "battery_status"},

    {"endpoint": "modes", "key": "data.mode", "name": "operating_mode"},
    {"endpoint": "modes", "key": "data.eco", "name": "economy_mode"},
    {"endpoint": "modes", "key": "data.offgrid_on", "name": "offgrid_on_hold"},
    {"endpoint": "modes", "key": "data.time_cfg", "name": "time_config"},
    {"endpoint": "modes", "key": "data.dod", "name": "depth_of_discharge"},
    {"endpoint": "modes", "key": "data.backup_charP", "name": "backup_charge_power"},


    {"endpoint": "control-panels", "key": "data.mode", "name": "mode"},
    {"endpoint": "control-panels", "key": "data.MI1", "name": "config"},



]
