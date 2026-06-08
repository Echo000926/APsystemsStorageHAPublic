"""ApsystemsStorage text platform for time slot configurations."""
import json
import logging
import re
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the time configuration text entities via config flow."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Instantiate Modes Time Config entity and attach to coordinator
    modes_time_config_text = APsystemsStorageModesTimeSlotsText(coordinator, entry)
    coordinator.modes_time_config_text_entity = modes_time_config_text

    # Instantiate Control Panels Config entity and attach to coordinator
    controlpanels_config_text = APsystemsStorageControlPanelsTimeSlotsText(coordinator, entry)
    coordinator.controlpanels_config_text_entity = controlpanels_config_text

    entities = [modes_time_config_text, controlpanels_config_text]
    async_add_entities(entities)


class APsystemsStorageModesTimeSlotsText(CoordinatorEntity, TextEntity):
    """Represents a text entity for handling mode time slot arrays."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_modes_time_config_text"
        # self._attr_name = "modes_time_config"
        self._base_name = "modes_time_config"
        self._attr_name = self._base_name
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

        # Limit max input length to prevent excessively large payloads
        self._attr_native_max = 255

        # Variable to hold pending configuration before manual dispatch
        self._pending_modes_time_config = None

    @property
    def name(self) -> str:
        """Return the name of the entity, appending a marker if there are pending changes."""
        if self._pending_modes_time_config is not None:
            return f"{self._base_name} *"
        return self._base_name

    @property
    def native_value(self) -> str | None:
        """Return the current time slot array as a JSON string."""
        if self._pending_modes_time_config is not None:
            return json.dumps(self._pending_modes_time_config, ensure_ascii=False)

        if self.coordinator.data is None:
            return "[]"

        time_cfg_text = self.coordinator.data.get("modes", {}).get("data", {}).get("time_cfg")
        if time_cfg_text:
            return json.dumps(time_cfg_text, ensure_ascii=False)

        return "[]"

    async def async_set_value(self, value: str) -> None:
        """Handle user input when modifying the text box in HA UI."""
        _LOGGER.debug("User attempting to update modes time configuration: %s", value)

        try:
            new_time_cfg_list = json.loads(value)

            # 1. Basic format validation: Ensure it's a non-empty list
            if not isinstance(new_time_cfg_list, list) or len(new_time_cfg_list) == 0:
                raise ValueError("Input must be an array containing configuration objects, e.g., [{\"E\":\"1\", ...}]")

            # Get the first configuration object (dictionary)
            config_obj = new_time_cfg_list[0]
            if not isinstance(config_obj, dict):
                raise ValueError("Elements inside the array must be objects (dictionaries)")

        except json.JSONDecodeError as e:
            _LOGGER.error("Invalid JSON format for modes time configuration: %s", e)
            return
        except ValueError as e:
            _LOGGER.error("Validation failed for modes time configuration: %s", e)
            return

        # 2. Deep content validation: Adapted for complex structures
        # Validate 'E' (Enable status, must be string "0" or "1")
        if "E" not in config_obj or config_obj["E"] not in ["0", "1"]:
            _LOGGER.error("Config error: Missing 'E' field or value is not '0'/'1'")
            return

        # Validate 'W' (Weekdays, must be a list)
        if "W" not in config_obj or not isinstance(config_obj["W"], list):
            _LOGGER.error("Config error: Missing 'W' field or 'W' is not an array format")
            return

        # Validate 'TM' (Time slots array, must be a list)
        if "TM" not in config_obj or not isinstance(config_obj["TM"], list):
            _LOGGER.error("Config error: Missing 'TM' field or 'TM' is not an array format")
            return

        # Further validate each time slot object within the 'TM' array
        for tm_item in config_obj["TM"]:
            if not isinstance(tm_item, dict):
                _LOGGER.error("Non-object element found in TM array: %s", tm_item)
                return

            # Validate 'F' (Start time/flag, assuming expected values are "0", "1", "2")
            if "F" not in tm_item or tm_item["F"] not in ["0", "1", "2"]:
                _LOGGER.error("Invalid start time flag F format: %s, must be '0', '1', or '2'", tm_item.get('F'))
                return

            # Validate 'T' (End time, must be 8-digit numeric string)
            if "T" not in tm_item or not re.match(r'^\d{8}$', tm_item["T"]):
                _LOGGER.error("Invalid end time T format: %s, must be 8 digits", tm_item.get('T'))
                return

            # Validate 'FI' (Power settings, must be a dictionary)
            if "FI" not in tm_item or not isinstance(tm_item["FI"], dict):
                _LOGGER.error("Missing FI configuration or invalid format: %s", tm_item.get('FI'))
                return

        # 3. Validation passed, temporarily store the data
        self._pending_modes_time_config = new_time_cfg_list
        self.async_write_ha_state()
        _LOGGER.info("Modes time configuration validated successfully. Stored locally, awaiting manual dispatch.")

    def clear_pending_data(self):
        """Clear the locally stored pending configuration."""
        self._pending_modes_time_config = None
        # Use thread-safe state update method recommended by Home Assistant
        self.schedule_update_ha_state()


class APsystemsStorageControlPanelsTimeSlotsText(CoordinatorEntity, TextEntity):
    """Represents a text entity for handling control panel time slot configurations."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_controlpanels_config_text"
        # self._attr_name = "controlpanels_config"
        self._base_name = "controlpanels_config"
        self._attr_name = self._base_name
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

        # Limit max input length to prevent excessively large payloads
        self._attr_native_max = 255

        # Variable to hold pending configuration before manual dispatch
        self._pending_controlpanels_config = None

    @property
    def name(self) -> str:
        """Return the name of the entity, appending a marker if there are pending changes."""
        if self._pending_controlpanels_config is not None:
            return f"{self._base_name} *"
        return self._base_name

    @property
    def native_value(self) -> str | None:
        """Return the current control panel configuration as a JSON string."""
        if self._pending_controlpanels_config is not None:
            return json.dumps(self._pending_controlpanels_config, ensure_ascii=False)

        if self.coordinator.data is None:
            return "{}"

        time_cfg_data = (
            self.coordinator.data.get("control-panels", {})
            .get("data", {})
            .get("MI1")
        )

        if time_cfg_data:
            return json.dumps(time_cfg_data, ensure_ascii=False)

        return "{}"

    async def async_set_value(self, value: str) -> None:
        """Handle user input when modifying the text box in HA UI."""
        _LOGGER.debug("User attempting to update control panels configuration: %s", value)

        try:
            new_time_cfg_dict = json.loads(value)

            # 1. Basic format validation: Ensure it's a non-empty dictionary
            if not isinstance(new_time_cfg_dict, dict) or len(new_time_cfg_dict) == 0:
                raise ValueError(
                    "Input must be a non-empty object format, e.g., {\"power\": [...], \"time\": [...]}"
                )

            # 2. Validate required internal list parameters
            required_list_keys = ["power", "time"]
            for key in required_list_keys:
                if key not in new_time_cfg_dict:
                    raise ValueError(f"Missing required list parameter in config object: '{key}'")

                param_value = new_time_cfg_dict[key]
                if not isinstance(param_value, list):
                    raise ValueError(f"Parameter '{key}' must be an array (List) format")

                if len(param_value) == 0:
                    raise ValueError(f"Parameter '{key}' cannot be an empty array")

        except json.JSONDecodeError as e:
            _LOGGER.error("Invalid JSON format for control panels configuration: %s", e)
            return
        except ValueError as e:
            _LOGGER.error("Validation failed for control panels configuration: %s", e)
            return

        # 3. Validation passed, temporarily store the data
        self._pending_controlpanels_config = new_time_cfg_dict
        self.async_write_ha_state()
        _LOGGER.info("Control panels configuration validated successfully. Stored locally, awaiting manual dispatch.")

    def clear_pending_data(self):
        """Clear the locally stored pending configuration."""
        self._pending_controlpanels_config = None
        # Use thread-safe state update method recommended by Home Assistant
        self.schedule_update_ha_state()