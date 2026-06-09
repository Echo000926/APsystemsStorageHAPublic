"""ApsystemsStorage button platform."""
import logging
import json
import aiohttp
import asyncio
import copy
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Mapping for operating mode dropdown labels to actual device values
MODES_OPERATING_MODE_MAP = {
    "Self-consumption Mode": "2",
    "Time-of-Use Mode": "3",
    "Backup Mode": "4",
}

# Mapping for power limit dropdown labels to actual device values
MODES_POWER_LIMIT_MAP = {
    "800W": "800",
    "2500W": "2500",
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up APsystemsStorage buttons from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        APsystemsStorageModesSettingsButton(coordinator, entry),
        APsystemsStorageControlpanelsSettingsButton(coordinator, entry),
    ]

    async_add_entities(entities)
    _LOGGER.info(
        "Successfully registered %d button entities for ApsystemsStorage",
        len(entities)
    )


class APsystemsStorageModesSettingsButton(CoordinatorEntity, ButtonEntity):
    """Represents a confirmation button to send unified mode settings to the device."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_modes_settings_button"
        self._attr_name = "Confirm Modes Settings"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    async def async_press(self) -> None:
        """Handle the button press from the frontend."""
        payload = {}

        # 1. Get current state of the Eco switch
        switch_state = self.hass.states.get("switch.modes_eco_switch")
        if switch_state and switch_state.state not in ("unknown", "unavailable"):
            is_eco_on = (switch_state.state == "on")
            payload["eco"] = "1" if is_eco_on else "0"
            _LOGGER.debug("Modes setting eco switch: %s", switch_state.state)

        # 2. Get current state of the Off-grid switch
        offgrid_on_state = self.hass.states.get("switch.modes_offgrid_on_switch")
        if offgrid_on_state and offgrid_on_state.state not in ("unknown", "unavailable"):
            is_offgrid_on = (offgrid_on_state.state == "on")
            payload["offgrid_on"] = "1" if is_offgrid_on else "0"
            _LOGGER.debug("Modes setting off-grid switch: %s", offgrid_on_state.state)

        # 3. Get current operating mode selection
        mode_str = self.hass.states.get("select.modes_operating_mode")
        if mode_str and mode_str.state not in ("unknown", "unavailable"):
            mode_value = MODES_OPERATING_MODE_MAP.get(mode_str.state)
            payload["mode"] = mode_value
            _LOGGER.debug("Modes setting operating mode: %s", mode_str.state)

        # 4. Get current power limit selection
        power_limit_str = self.hass.states.get("select.modes_power_limit")
        if power_limit_str and power_limit_str.state not in ("unknown", "unavailable"):
            power_limit_value = MODES_POWER_LIMIT_MAP.get(power_limit_str.state)
            payload["power_limit"] = power_limit_value
            _LOGGER.debug("Modes setting power limit: %s", power_limit_str.state)

        # 5. Get Depth of Discharge (DoD) value
        dod_value = self.hass.states.get("number.modes_dod")
        if dod_value and dod_value.state not in ("unknown", "unavailable"):
            payload["dod"] = dod_value.state
            _LOGGER.debug("Modes setting DoD: %s", dod_value.state)

        #
        backup_charge_power_value = self.hass.states.get("number.modes_backup_charge_power")
        if backup_charge_power_value and backup_charge_power_value.state not in ("unknown", "unavailable"):
            payload["backup_charP"] = backup_charge_power_value.state
            _LOGGER.debug("Modes setting backup_charP: %s", backup_charge_power_value.state)

        # 6. Get time configuration strategy
        time_cfg_str = self.hass.states.get("text.modes_time_config")
        if time_cfg_str and time_cfg_str.state not in ("unknown", "unavailable"):
            try:
                real_data = json.loads(time_cfg_str.state)
                payload["time_cfg"] = real_data
                _LOGGER.debug("Parsed time configuration data successfully.")
            except json.JSONDecodeError as e:
                _LOGGER.error("Failed to parse time configuration JSON: %s", e)

        _LOGGER.info("Assembled dynamic payload for modes settings: %s", payload)

        host = self._entry.data.get("host") or self._entry.data.get("ip")
        port = self._entry.data.get("port", 80)
        base_url = f"http://{host}:{port}"
        url = f"{base_url}/modes"

        session = async_get_clientsession(self.hass)

        try:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    try:
                        json_data = await response.json()
                        return_code = json_data.get("code", 201)
                    except Exception:
                        return_code = 201

                    if return_code == 200:
                        _LOGGER.info("Modes configuration sent successfully. Device returned code: %s", return_code)
                        await self.hass.services.async_call(
                            "persistent_notification",
                            "create",
                            {
                                "title": "Modes Configuration Result",
                                "message": "**Modes configuration has been successfully written to the device!**",
                                "notification_id": "modes_config_feedback"
                            }
                        )
                    else:
                        _LOGGER.error("Modes configuration failed! Device rejected the request.")
                        await self.hass.services.async_call(
                            "persistent_notification",
                            "create",
                            {
                                "title": "Modes Configuration Result",
                                "message": "**Modes configuration failed!**\nThe device rejected the execution or parameters are invalid.",
                                "notification_id": "modes_config_feedback"
                            }
                        )
                else:
                    error_text = await response.text()
                    _LOGGER.error("Modes configuration request failed with HTTP status: %s", response.status)
                    await self.hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": "Modes Configuration Failed",
                            "message": f"HTTP Status Code: {response.status}\nDetails: {error_text}",
                            "notification_id": "modes_config_feedback"
                        }
                    )

        except Exception as err:
            _LOGGER.exception("Network exception during modes configuration request: %s", err)
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Modes Configuration Exception",
                    "message": f"An unexpected error occurred: {err}",
                    "notification_id": "modes_config_feedback"
                }
            )

        finally:
            # --- Key Change: Always refresh after request completes (success or failure) ---
            _LOGGER.debug("Request completed. Triggering coordinator refresh...")

            if hasattr(self.coordinator, "data") and self.coordinator.data is not None:
                new_data = copy.deepcopy(self.coordinator.data)

                if "modes" in new_data and "data" in new_data["modes"]:
                    new_data["modes"]["data"] = payload

                self.coordinator.async_set_updated_data(new_data)
                _LOGGER.info("Bulk optimistically updated coordinator data with full payload.")


            # 2. 数据刷新完成后，再清除所有相关实体的 pending 状态
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


            # 1. 先触发立即刷新，等待 Coordinator 获取设备的最新真实状态
            if hasattr(self.coordinator, "refresh_data"):
                await self.coordinator.refresh_data()

            _LOGGER.info("Refreshed data and cleared pending states for all modes-related entities.")


class APsystemsStorageControlpanelsSettingsButton(CoordinatorEntity, ButtonEntity):
    """Represents a confirmation button to send unified control panel settings to the device."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_controlpanels_settings_button"
        self._attr_name = "Confirm Control Panels Settings"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    async def async_press(self) -> None:
        """Handle the button press from the frontend."""
        payload = {}

        # 1. Get current state of the mode switch
        mode_state = self.hass.states.get("switch.controlpanels_mode_switch")
        if mode_state and mode_state.state not in ("unknown", "unavailable"):
            is_enable = (mode_state.state == "on")
            payload["mode"] = "1" if is_enable else "0"
            _LOGGER.debug("Control panels setting mode: %s", mode_state.state)

        # 2. Get time configuration strategy
        time_cfg_str = self.hass.states.get("text.controlpanels_config")
        _LOGGER.debug("Control panels setting time raw value: %s", time_cfg_str)

        if time_cfg_str and time_cfg_str.state not in ("unknown", "unavailable"):
            try:
                real_data = json.loads(time_cfg_str.state)
                payload["MI1"] = real_data
                _LOGGER.debug("Parsed control panels time configuration data successfully.")
            except json.JSONDecodeError as e:
                _LOGGER.error("Failed to parse control panels time configuration JSON: %s", e)

        _LOGGER.info("Assembled dynamic payload for control panels settings: %s", payload)

        host = self._entry.data.get("host") or self._entry.data.get("ip")
        port = self._entry.data.get("port", 80)
        base_url = f"http://{host}:{port}"
        url = f"{base_url}/control-panels"

        session = async_get_clientsession(self.hass)

        try:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    try:
                        json_data = await response.json()
                        return_code = json_data.get("code", 201)
                    except Exception:
                        return_code = 201

                    if return_code == 200:
                        _LOGGER.info("Control panels configuration sent successfully. Device returned code: %s",
                                     return_code)
                        await self.hass.services.async_call(
                            "persistent_notification",
                            "create",
                            {
                                "title": "Control Panels Configuration Result",
                                "message": "**Control panels configuration has been successfully written to the device!**",
                                "notification_id": "controlpanels_config_feedback"
                            }
                        )
                    else:
                        _LOGGER.error("Control panels configuration failed! Device rejected the request.")
                        await self.hass.services.async_call(
                            "persistent_notification",
                            "create",
                            {
                                "title": "Control Panels Configuration Result",
                                "message": "**Control panels configuration failed!**\nThe device rejected the execution or parameters are invalid.",
                                "notification_id": "controlpanels_config_feedback"
                            }
                        )
                else:
                    error_text = await response.text()
                    _LOGGER.error("Control panels configuration request failed with HTTP status: %s", response.status)
                    await self.hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": "Control Panels Configuration Failed",
                            "message": f"HTTP Status Code: {response.status}\nDetails: {error_text}",
                            "notification_id": "controlpanels_config_feedback"
                        }
                    )

        except Exception as err:
            _LOGGER.exception("Network exception during control panels configuration request: %s", err)
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Control Panels Configuration Exception",
                    "message": f"An unexpected error occurred: {err}",
                    "notification_id": "controlpanels_config_feedback"
                }
            )

        finally:
            # --- Core Optimization: Zero-delay bulk optimistic update ---
            _LOGGER.debug("Request completed. Performing bulk optimistic update...")

            # 1. 直接将本次提交的完整 payload 覆盖到 Coordinator 对应的数据节点
            if hasattr(self.coordinator, "data") and self.coordinator.data is not None:
                new_data = copy.deepcopy(self.coordinator.data)

                # 将 payload 整体替换到 controlpanels -> data 层级
                if "controlpanels" in new_data and "data" in new_data["controlpanels"]:
                    new_data["controlpanels"]["data"] = payload

                # 主动推送新数据给 Coordinator，立即触发 UI 无缝刷新
                self.coordinator.async_set_updated_data(new_data)
                _LOGGER.info("Bulk optimistically updated coordinator data with full payload.")

            # 2. 安全地清除所有相关实体的 pending 状态
            entity_mappings = [
                ("controlpanels_mode_switch_entity", "Mode switch"),
                ("controlpanels_config_text_entity", "Time config text"),
            ]

            for attr_name, _ in entity_mappings:
                entity = getattr(self.coordinator, attr_name, None)
                if entity:
                    entity.clear_pending_data()

            # 3. 在后台静默发起一次真实刷新，确保最终与物理设备的真实状态保持绝对一致
            if hasattr(self.coordinator, "refresh_data"):
                self.hass.async_create_task(self.coordinator.refresh_data())

            _LOGGER.info("Cleared pending states for all control panels-related entities.")
            # ---------------------------------------------------------------------------