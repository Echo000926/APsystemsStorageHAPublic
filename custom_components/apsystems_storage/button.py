"""APsystems Storage button platform."""
from __future__ import annotations

import copy
import json
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .apsystems_api import APsystemsStorageApiClient, APsystemsStorageApiError
from .const import CONF_IP, DEFAULT_PORT, DOMAIN, MANUFACTURER, MODEL
from .coordinator import APsystemsStorageCoordinator

_LOGGER = logging.getLogger(__name__)

# Mapping for operating mode snake_case option keys to actual device values
MODES_OPERATING_MODE_MAP = {
    "self_consumption_mode": "2",
    "time_of_use_mode": "3",
    "backup_mode": "4",
}

# Mapping for power limit snake_case option keys to actual device values
MODES_POWER_LIMIT_MAP = {
    "800w": "800",
    "2500w": "2500",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up APsystems Storage button entities from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.
        async_add_entities: Callback to add entities.

    """
    coordinator: APsystemsStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        APsystemsStorageModesSettingsButton(
            coordinator=coordinator, entry_id=entry.entry_id
        ),
        APsystemsStorageControlPanelsSettingsButton(
            coordinator=coordinator, entry_id=entry.entry_id
        ),
    ]

    async_add_entities(entities)
    _LOGGER.info(
        "Successfully registered %d button entities for APsystems Storage",
        len(entities),
    )


class APsystemsStorageModesSettingsButton(
    CoordinatorEntity[APsystemsStorageCoordinator], ButtonEntity
):
    """Button entity to send unified mode settings to the device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the modes settings button.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = ButtonEntityDescription(
            key="modes_settings_button",
            translation_key="confirm_modes_settings",
            name="Confirm Modes Settings",
            entity_category=EntityCategory.CONFIG,
        )
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_modes_settings_button"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }

    async def async_press(self) -> None:
        """Handle the button press from the frontend."""
        payload: dict[str, Any] = {}

        # 1. Get current state of the Eco switch
        switch_state = self.hass.states.get("switch.apsystems_storage_eco_mode")
        if switch_state and switch_state.state not in ("unknown", "unavailable"):
            is_eco_on = switch_state.state == "on"
            payload["eco"] = "1" if is_eco_on else "0"
            _LOGGER.debug("Modes setting eco switch: %s", switch_state.state)

        # 2. Get current state of the Off-grid switch
        offgrid_on_state = self.hass.states.get("switch.apsystems_storage_off_grid_on_hold")
        if offgrid_on_state and offgrid_on_state.state not in ("unknown", "unavailable"):
            is_offgrid_on = offgrid_on_state.state == "on"
            payload["offgrid_on"] = "1" if is_offgrid_on else "0"
            _LOGGER.debug("Modes setting off-grid switch: %s", offgrid_on_state.state)

        # 3. Get current operating mode selection
        mode_str = self.hass.states.get("select.apsystems_storage_operating_mode")
        if mode_str and mode_str.state not in ("unknown", "unavailable"):
            mode_value = MODES_OPERATING_MODE_MAP.get(mode_str.state)
            payload["mode"] = mode_value
            _LOGGER.debug("Modes setting operating mode: %s", mode_str.state)

        # 4. Get current power limit selection
        power_limit_str = self.hass.states.get("select.apsystems_storage_power_limit")
        if power_limit_str and power_limit_str.state not in ("unknown", "unavailable"):
            power_limit_value = MODES_POWER_LIMIT_MAP.get(power_limit_str.state)
            payload["power_limit"] = power_limit_value
            _LOGGER.debug("Modes setting power limit: %s", power_limit_str.state)

        # 5. Get Depth of Discharge (DoD) value
        dod_value = self.hass.states.get("number.apsystems_storage_depth_of_discharge")
        if dod_value and dod_value.state not in ("unknown", "unavailable"):
            payload["dod"] = dod_value.state
            _LOGGER.debug("Modes setting DoD: %s", dod_value.state)

        # 6. Get backup charge power value
        backup_charge_power_value = self.hass.states.get(
            "number.apsystems_storage_backup_charge_power"
        )
        if backup_charge_power_value and backup_charge_power_value.state not in (
            "unknown",
            "unavailable",
        ):
            payload["backup_charP"] = backup_charge_power_value.state
            _LOGGER.debug("Modes setting backup_charP: %s", backup_charge_power_value.state)

        # 7. Get time configuration strategy
        time_cfg_str = self.hass.states.get("text.apsystems_storage_time_configuration")
        if time_cfg_str and time_cfg_str.state not in ("unknown", "unavailable"):
            try:
                real_data = json.loads(time_cfg_str.state)
                payload["time_cfg"] = real_data
                _LOGGER.debug("Parsed time configuration data successfully.")
            except json.JSONDecodeError as e:
                _LOGGER.error("Failed to parse time configuration JSON: %s", e)

        _LOGGER.info("Assembled dynamic payload for modes settings: %s", payload)

        # Send the payload using the API client
        try:
            json_data = await self.coordinator.api_client.async_post_data("modes", payload)
            return_code = json_data.get("code", 201)

            if return_code == 200:
                _LOGGER.info(
                    "Modes configuration sent successfully. Device returned code: %s",
                    return_code,
                )
                await self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Modes Configuration Result",
                        "message": "**Modes configuration has been successfully written to the device!**",
                        "notification_id": "modes_config_feedback",
                    },
                )
            else:
                _LOGGER.error("Modes configuration failed! Device rejected the request.")
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="modes_config_failed",
                )
        except APsystemsStorageApiError as err:
            _LOGGER.error("Modes configuration request failed: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
                translation_placeholders={"error": str(err)},
            ) from err

        finally:
            # Optimistic update: push payload to coordinator data
            if hasattr(self.coordinator, "data") and self.coordinator.data is not None:
                new_data = copy.deepcopy(self.coordinator.data)
                if "modes" in new_data and "data" in new_data["modes"]:
                    new_data["modes"]["data"] = payload
                self.coordinator.async_set_updated_data(new_data)
                _LOGGER.info("Bulk optimistically updated coordinator data with full payload.")

            # Clear all related entities' pending states
            entity_mappings = [
                ("modes_backup_charge_power_number_entity", "backup charge power number"),
                ("modes_dod_number_entity", "DoD number"),
                ("modes_mode_select_entity", "Operating mode select"),
                ("modes_power_limit_select_entity", "Power limit select"),
                ("modes_eco_switch_entity", "Eco switch"),
                ("modes_offgrid_on_switch_entity", "Off-grid switch"),
                ("modes_time_config_text_entity", "Time config text"),
            ]

            for attr_name, display_name in entity_mappings:
                entity = getattr(self.coordinator, attr_name, None)
                if entity:
                    entity.clear_pending_data()

            # Trigger immediate refresh to get real device state
            await self.coordinator.async_request_refresh_now()
            _LOGGER.info("Refreshed data and cleared pending states for all modes-related entities.")


class APsystemsStorageControlPanelsSettingsButton(
    CoordinatorEntity[APsystemsStorageCoordinator], ButtonEntity
):
    """Button entity to send unified control panel settings to the device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the control panels settings button.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = ButtonEntityDescription(
            key="controlpanels_settings_button",
            translation_key="confirm_control_panels_settings",
            name="Confirm Control Panels Settings",
            entity_category=EntityCategory.CONFIG,
        )
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_controlpanels_settings_button"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }

    async def async_press(self) -> None:
        """Handle the button press from the frontend."""
        payload: dict[str, Any] = {}

        # 1. Get current state of the mode switch
        mode_state = self.hass.states.get("switch.apsystems_storage_control_panel_mode")
        if mode_state and mode_state.state not in ("unknown", "unavailable"):
            is_enable = mode_state.state == "on"
            payload["mode"] = "1" if is_enable else "0"
            _LOGGER.debug("Control panels setting mode: %s", mode_state.state)

        # 2. Get time configuration strategy
        time_cfg_str = self.hass.states.get(
            "text.apsystems_storage_control_panel_configuration"
        )
        _LOGGER.debug("Control panels setting time raw value: %s", time_cfg_str)

        if time_cfg_str and time_cfg_str.state not in ("unknown", "unavailable"):
            try:
                real_data = json.loads(time_cfg_str.state)
                payload["MI1"] = real_data
                _LOGGER.debug("Parsed control panels time configuration data successfully.")
            except json.JSONDecodeError as e:
                _LOGGER.error("Failed to parse control panels time configuration JSON: %s", e)

        _LOGGER.info("Assembled dynamic payload for control panels settings: %s", payload)

        # Send the payload using the API client
        try:
            json_data = await self.coordinator.api_client.async_post_data(
                "control-panels", payload
            )
            return_code = json_data.get("code", 201)

            if return_code == 200:
                _LOGGER.info(
                    "Control panels configuration sent successfully. Device returned code: %s",
                    return_code,
                )
                await self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Control Panels Configuration Result",
                        "message": "**Control panels configuration has been successfully written to the device!**",
                        "notification_id": "controlpanels_config_feedback",
                    },
                )
            else:
                _LOGGER.error("Control panels configuration failed! Device rejected the request.")
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="control_panels_config_failed",
                )
        except APsystemsStorageApiError as err:
            _LOGGER.error("Control panels configuration request failed: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
                translation_placeholders={"error": str(err)},
            ) from err

        finally:
            # Optimistic update: push payload to coordinator data
            if hasattr(self.coordinator, "data") and self.coordinator.data is not None:
                new_data = copy.deepcopy(self.coordinator.data)
                if "controlpanels" in new_data and "data" in new_data["controlpanels"]:
                    new_data["controlpanels"]["data"] = payload
                self.coordinator.async_set_updated_data(new_data)
                _LOGGER.info("Bulk optimistically updated coordinator data with full payload.")

            # Clear all related entities' pending states
            entity_mappings = [
                ("controlpanels_mode_switch_entity", "Mode switch"),
                ("controlpanels_config_text_entity", "Time config text"),
            ]

            for attr_name, _ in entity_mappings:
                entity = getattr(self.coordinator, attr_name, None)
                if entity:
                    entity.clear_pending_data()

            # Trigger background refresh to sync with real device state
            self.hass.async_create_task(self.coordinator.async_request_refresh_now())
            _LOGGER.info("Cleared pending states for all control panels-related entities.")
