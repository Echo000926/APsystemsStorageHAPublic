"""ApsystemsStorage modes select platform."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the mode and power limit select entities via config flow."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Instantiate Mode Select entity and attach to coordinator
    modes_mode_select = APsystemsStorageModesModeSelect(coordinator, entry)
    coordinator.modes_mode_select_entity = modes_mode_select

    # Instantiate Power Limit Select entity and attach to coordinator
    modes_power_limit_select = APsystemsStorageModesPowerLimitSelect(coordinator, entry)
    coordinator.modes_power_limit_select_entity = modes_power_limit_select

    entities = [modes_mode_select, modes_power_limit_select]
    async_add_entities(entities)


class APsystemsStorageModesModeSelect(CoordinatorEntity, SelectEntity):
    """Represents a select entity for operating modes."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_modes_mode_select"
        self._base_name = "modes_operating_mode"
        self._attr_name = self._base_name
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

        # Options displayed in the frontend
        self._mode_display_options = ["AI Mode", "Self-consumption Mode", "Time-of-Use Mode", "Backup Mode"]

        # Mapping from frontend display options to backend API values
        # Note: "IDLE" (0) and "AI Mode" (1) are not supported by this interface 
        # and are intentionally excluded from the frontend.
        self._mode_option_to_value_map = {
            "IDLE": "0",
            "AI Mode": "1",
            "Self-consumption Mode": "2",
            "Time-of-Use Mode": "3",
            "Backup Mode": "4"
        }
        self._mode_value_to_option_map = {v: k for k, v in self._mode_option_to_value_map.items()}

        # Variable to hold pending option before manual dispatch
        self._pending_mode_option = None


    @property
    def name(self) -> str:
        """Return the name of the entity, appending a marker if there are pending changes."""
        if self._pending_mode_option is not None:
            return f"{self._base_name} *"
        return self._base_name

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

        real_mode = self.coordinator.data.get("modes", {}).get("data", {}).get("mode")
        return self._mode_value_to_option_map.get(real_mode)

    async def async_select_option(self, option: str) -> None:
        """Handle user selection of an operating mode in the HA UI."""
        _LOGGER.debug("User selected operating mode: %s", option)
        self._pending_mode_option = option
        self.async_write_ha_state()

    def clear_pending_data(self):
        """Clear the locally stored pending mode option."""
        self._pending_mode_option = None
        # Use thread-safe state update method recommended by Home Assistant
        self.schedule_update_ha_state()


class APsystemsStorageModesPowerLimitSelect(CoordinatorEntity, SelectEntity):
    """Represents a select entity for power limits."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_modes_power_limit_select"
        # self._attr_name = "modes_power_limit"
        self._base_name = "modes_power_limit"
        self._attr_name = self._base_name
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

        # Options displayed in the frontend
        self._power_limit_display_options = ["800W", "2500W"]

        # Mapping from frontend display options to backend API values
        self._power_limit_option_to_value_map = {"800W": "800", "2500W": "2500"}
        self._power_limit_value_to_option_map = {v: k for k, v in self._power_limit_option_to_value_map.items()}

        # Variable to hold pending option before manual dispatch
        self._pending_power_limit_option = None

    @property
    def name(self) -> str:
        """Return the name of the entity, appending a marker if there are pending changes."""
        if self._pending_power_limit_option is not None:
            return f"{self._base_name} *"
        return self._base_name

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

        real_value = self.coordinator.data.get("modes", {}).get("data", {}).get("power_limit")
        return self._power_limit_value_to_option_map.get(real_value)

    async def async_select_option(self, option: str) -> None:
        """Handle user selection of a power limit in the HA UI."""
        _LOGGER.debug("User selected power limit: %s", option)
        self._pending_power_limit_option = option
        self.async_write_ha_state()

    def clear_pending_data(self):
        """Clear the locally stored pending power limit option."""
        self._pending_power_limit_option = None
        # Use thread-safe state update method recommended by Home Assistant
        self.schedule_update_ha_state()