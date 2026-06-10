"""APsystems Storage text platform for time slot configurations."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import APsystemsStorageCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up APsystems Storage text entities from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.
        async_add_entities: Callback to add entities.

    """
    coordinator: APsystemsStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        APsystemsStorageModesTimeSlotsText(coordinator=coordinator, entry_id=entry.entry_id),
        APsystemsStorageControlPanelsTimeSlotsText(
            coordinator=coordinator, entry_id=entry.entry_id
        ),
    ]

    # Attach entities to coordinator for later pending state management
    coordinator.modes_time_config_text_entity = entities[0]
    coordinator.controlpanels_config_text_entity = entities[1]

    async_add_entities(entities)


class APsystemsStorageModesTimeSlotsText(
    CoordinatorEntity[APsystemsStorageCoordinator], TextEntity
):
    """Text entity for handling mode time slot arrays."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the modes time config text entity.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = TextEntityDescription(
            key="modes_time_config",
            translation_key="time_configuration",
            name="Time Configuration",
            native_max=255,
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_modes_time_config_text"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }
        self._pending_modes_time_config: list[dict[str, Any]] | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes."""
        if self._pending_modes_time_config is not None:
            return f"{self.entity_description.name} *"
        return None  # Let HA use translation_key from entity description

    @property
    def native_value(self) -> str:
        """Return the current time slot array as a JSON string."""
        if self._pending_modes_time_config is not None:
            return json.dumps(self._pending_modes_time_config, ensure_ascii=False)

        if self.coordinator.data is None:
            return "[]"

        time_cfg_text = (
            self.coordinator.data.get("modes", {}).get("data", {}).get("time_cfg")
        )
        if time_cfg_text:
            return json.dumps(time_cfg_text, ensure_ascii=False)

        return "[]"

    async def async_set_value(self, value: str) -> None:
        """Handle user input when modifying the text box in HA UI.

        Args:
            value: The new text value entered by the user.

        """
        _LOGGER.debug("User attempting to update modes time configuration: %s", value)

        try:
            new_time_cfg_list = json.loads(value)

            # Basic format validation: Ensure it's a non-empty list
            if not isinstance(new_time_cfg_list, list) or len(new_time_cfg_list) == 0:
                raise ValueError(
                    "Input must be an array containing configuration objects, "
                    'e.g., [{"E":"1", ...}]'
                )

            # Get the first configuration object
            config_obj = new_time_cfg_list[0]
            if not isinstance(config_obj, dict):
                raise ValueError("Elements inside the array must be objects (dictionaries)")

        except json.JSONDecodeError as e:
            _LOGGER.error("Invalid JSON format for modes time configuration: %s", e)
            return
        except ValueError as e:
            _LOGGER.error("Validation failed for modes time configuration: %s", e)
            return

        # Deep content validation
        if "E" not in config_obj or config_obj["E"] not in ["0", "1"]:
            _LOGGER.error("Config error: Missing 'E' field or value is not '0'/'1'")
            return

        if "W" not in config_obj or not isinstance(config_obj["W"], list):
            _LOGGER.error("Config error: Missing 'W' field or 'W' is not an array format")
            return

        if "TM" not in config_obj or not isinstance(config_obj["TM"], list):
            _LOGGER.error("Config error: Missing 'TM' field or 'TM' is not an array format")
            return

        for tm_item in config_obj["TM"]:
            if not isinstance(tm_item, dict):
                _LOGGER.error("Non-object element found in TM array: %s", tm_item)
                return

            if "F" not in tm_item or tm_item["F"] not in ["0", "1", "2"]:
                _LOGGER.error(
                    "Invalid start time flag F format: %s, must be '0', '1', or '2'",
                    tm_item.get("F"),
                )
                return

            if "T" not in tm_item or not re.match(r"^\d{8}$", tm_item["T"]):
                _LOGGER.error(
                    "Invalid end time T format: %s, must be 8 digits",
                    tm_item.get("T"),
                )
                return

            if "FI" not in tm_item or not isinstance(tm_item["FI"], dict):
                _LOGGER.error(
                    "Missing FI configuration or invalid format: %s",
                    tm_item.get("FI"),
                )
                return

        # Validation passed, temporarily store the data
        self._pending_modes_time_config = new_time_cfg_list
        self.async_write_ha_state()
        _LOGGER.info(
            "Modes time configuration validated successfully. "
            "Stored locally, awaiting manual dispatch."
        )

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending configuration."""
        self._pending_modes_time_config = None
        self.schedule_update_ha_state()


class APsystemsStorageControlPanelsTimeSlotsText(
    CoordinatorEntity[APsystemsStorageCoordinator], TextEntity
):
    """Text entity for handling control panel time slot configurations."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the control panels config text entity.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = TextEntityDescription(
            key="controlpanels_config",
            translation_key="control_panel_configuration",
            name="Control Panel Configuration",
            native_max=255,
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_controlpanels_config_text"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }
        self._pending_controlpanels_config: dict[str, Any] | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes."""
        if self._pending_controlpanels_config is not None:
            return f"{self.entity_description.name} *"
        return None  # Let HA use translation_key from entity description

    @property
    def native_value(self) -> str:
        """Return the current control panel configuration as a JSON string."""
        if self._pending_controlpanels_config is not None:
            return json.dumps(self._pending_controlpanels_config, ensure_ascii=False)

        if self.coordinator.data is None:
            return "{}"

        time_cfg_data = (
            self.coordinator.data.get("control-panels", {}).get("data", {}).get("MI1")
        )
        if time_cfg_data:
            return json.dumps(time_cfg_data, ensure_ascii=False)

        return "{}"

    async def async_set_value(self, value: str) -> None:
        """Handle user input when modifying the text box in HA UI.

        Args:
            value: The new text value entered by the user.

        """
        _LOGGER.debug("User attempting to update control panels configuration: %s", value)

        try:
            new_time_cfg_dict = json.loads(value)

            # Basic format validation: Ensure it's a non-empty dictionary
            if not isinstance(new_time_cfg_dict, dict) or len(new_time_cfg_dict) == 0:
                raise ValueError(
                    "Input must be a non-empty object format, e.g., "
                    '{"power": [...], "time": [...]}'
                )

            # Validate required internal list parameters
            required_list_keys = ["power", "time"]
            for key in required_list_keys:
                if key not in new_time_cfg_dict:
                    raise ValueError(
                        f"Missing required list parameter in config object: '{key}'"
                    )

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

        # Validation passed, temporarily store the data
        self._pending_controlpanels_config = new_time_cfg_dict
        self.async_write_ha_state()
        _LOGGER.info(
            "Control panels configuration validated successfully. "
            "Stored locally, awaiting manual dispatch."
        )

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending configuration."""
        self._pending_controlpanels_config = None
        self.schedule_update_ha_state()
