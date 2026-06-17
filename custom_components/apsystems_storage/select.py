"""APsystems Storage select platform."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
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
    """Set up APsystems Storage select entities from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.
        async_add_entities: Callback to add entities.

    """
    coordinator: APsystemsStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        APsystemsStorageModesModeSelect(coordinator=coordinator, entry_id=entry.entry_id),
        APsystemsStorageModesPowerLimitSelect(coordinator=coordinator, entry_id=entry.entry_id),
    ]

    # Attach entities to coordinator for later pending state management
    coordinator.modes_mode_select_entity = entities[0]
    coordinator.modes_power_limit_select_entity = entities[1]

    async_add_entities(entities)


class APsystemsStorageModesModeSelect(
    CoordinatorEntity[APsystemsStorageCoordinator], SelectEntity
):
    """Select entity for operating modes."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the operating mode select.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = SelectEntityDescription(
            key="modes_operating_mode",
            translation_key="operating_mode",
            name="Operating Mode",
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_modes_mode_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }

        # Options use snake_case keys; HA translates via strings.json
        self._mode_display_options = [
            "ai_mode",
            "self_consumption_mode",
            "time_of_use_mode",
            "backup_mode",
        ]

        # Mapping from snake_case option key to backend API values
        self._mode_option_to_value_map: dict[str, str] = {
            "ai_mode": "1",
            "self_consumption_mode": "2",
            "time_of_use_mode": "3",
            "backup_mode": "4",
        }
        self._mode_value_to_option_map: dict[str, str] = {
            v: k for k, v in self._mode_option_to_value_map.items()
        }

        self._pending_mode_option: str | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes."""
        if self._pending_mode_option is not None:
            return f"{self.entity_description.name} *"
        return f"{self.entity_description.name}"

    @property
    def options(self) -> list[str]:
        """Return the available operating modes."""
        return self._mode_display_options

    @property
    def current_option(self) -> str | None:
        """Return the currently selected operating mode."""
        if self._pending_mode_option is not None:
            return self._pending_mode_option

        if self.coordinator.data is None:
            return None

        real_mode = (
            self.coordinator.data.get("modes", {}).get("data", {}).get("mode")
        )
        return self._mode_value_to_option_map.get(real_mode)

    async def async_select_option(self, option: str) -> None:
        """Handle user selection of an operating mode in the HA UI."""
        _LOGGER.debug("User selected operating mode: %s", option)
        self._pending_mode_option = option
        self.async_write_ha_state()

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending mode option."""
        self._pending_mode_option = None
        self.schedule_update_ha_state()


class APsystemsStorageModesPowerLimitSelect(
    CoordinatorEntity[APsystemsStorageCoordinator], SelectEntity
):
    """Select entity for power limits."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the power limit select.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = SelectEntityDescription(
            key="modes_power_limit",
            translation_key="power_limit",
            name="Power Limit",
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_modes_power_limit_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }

        # Options use snake_case keys; HA translates via strings.json
        self._power_limit_display_options = ["800w", "2500w"]

        # Mapping from snake_case option key to backend API values
        self._power_limit_option_to_value_map: dict[str, str] = {
            "800w": "800",
            "2500w": "2500",
        }
        self._power_limit_value_to_option_map: dict[str, str] = {
            v: k for k, v in self._power_limit_option_to_value_map.items()
        }

        self._pending_power_limit_option: str | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes."""
        if self._pending_power_limit_option is not None:
            return f"{self.entity_description.name} *"
        return f"{self.entity_description.name}"

    @property
    def options(self) -> list[str]:
        """Return the available power limits."""
        return self._power_limit_display_options

    @property
    def current_option(self) -> str | None:
        """Return the currently selected power limit."""
        if self._pending_power_limit_option is not None:
            return self._pending_power_limit_option

        if self.coordinator.data is None:
            return None

        real_value = (
            self.coordinator.data.get("modes", {}).get("data", {}).get("power_limit")
        )
        return self._power_limit_value_to_option_map.get(real_value)

    async def async_select_option(self, option: str) -> None:
        """Handle user selection of a power limit in the HA UI."""
        _LOGGER.debug("User selected power limit: %s", option)
        self._pending_power_limit_option = option
        self.async_write_ha_state()

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending power limit option."""
        self._pending_power_limit_option = None
        self.schedule_update_ha_state()
