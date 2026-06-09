"""APsystemsStorage switch platform."""
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch entities via config flow."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Instantiate Eco Switch entity and attach to coordinator
    modes_eco_switch = APsystemsStorageModesEcoSwitch(coordinator, entry)
    coordinator.modes_eco_switch_entity = modes_eco_switch

    # Instantiate Offgrid On Switch entity and attach to coordinator
    modes_offgrid_on_switch = APsystemsStorageModesOffgridOnSwitch(coordinator, entry)
    coordinator.modes_offgrid_on_switch_entity = modes_offgrid_on_switch

    # Instantiate Control Panels Mode Switch entity and attach to coordinator
    controlpanels_mode_switch = APsystemsStorageControlPanelsModeSwitch(coordinator, entry)
    coordinator.controlpanels_mode_switch_entity = controlpanels_mode_switch

    entities = [
        modes_eco_switch,
        modes_offgrid_on_switch,
        controlpanels_mode_switch,
    ]

    async_add_entities(entities)


class APsystemsStorageModesEcoSwitch(CoordinatorEntity, SwitchEntity):
    """Virtual parameter switch (state automatically syncs with device reported data)."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_modes_eco_switch"
        # self._attr_name = "modes_eco_switch"
        self._base_name = "modes_eco_switch"
        self._attr_name = self._base_name
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

        # Variable to hold pending state before manual dispatch
        self._pending_state = None

    @property
    def name(self) -> str:
        """Return the name of the entity, appending a marker if there are pending changes."""
        if self._pending_state is not None:
            return f"{self._base_name} *"
        return self._base_name

    @property
    def is_on(self) -> bool:
        """Return the current eco status from the coordinator's real-time data."""
        if self._pending_state is not None:
            return self._pending_state

        if self.coordinator.data is None:
            return False

        eco_status = self.coordinator.data.get("modes", {}).get("data", {}).get("eco")
        return eco_status == "1"

    async def async_turn_on(self, **kwargs) -> None:
        """Handle user turning on the switch in HA UI (stores locally without sending command)."""
        self._pending_state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Handle user turning off the switch in HA UI (stores locally without sending command)."""
        self._pending_state = False
        self.async_write_ha_state()

    def clear_pending_data(self):
        """Clear the locally stored pending state."""
        self._pending_state = None
        # Use thread-safe state update method recommended by Home Assistant
        self.schedule_update_ha_state()


class APsystemsStorageModesOffgridOnSwitch(CoordinatorEntity, SwitchEntity):
    """Virtual parameter switch (state automatically syncs with device reported data)."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_modes_offgrid_on_switch"
        # self._attr_name = "modes_offgrid_on_switch"
        self._base_name = "modes_offgrid_on_switch"
        self._attr_name = self._base_name
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

        # Variable to hold pending state before manual dispatch
        self._pending_state = None

    @property
    def name(self) -> str:
        """Return the name of the entity, appending a marker if there are pending changes."""
        if self._pending_state is not None:
            return f"{self._base_name} *"
        return self._base_name

    @property
    def is_on(self) -> bool:
        """Return the current offgrid-on status from the coordinator's real-time data."""
        if self._pending_state is not None:
            return self._pending_state

        if self.coordinator.data is None:
            return False

        offgrid_on_status = self.coordinator.data.get("modes", {}).get("data", {}).get("offgrid_on")
        return offgrid_on_status == "1"

    async def async_turn_on(self, **kwargs) -> None:
        """Handle user turning on the switch in HA UI (stores locally without sending command)."""
        self._pending_state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Handle user turning off the switch in HA UI (stores locally without sending command)."""
        self._pending_state = False
        self.async_write_ha_state()

    def clear_pending_data(self):
        """Clear the locally stored pending state."""
        self._pending_state = None
        # Use thread-safe state update method recommended by Home Assistant
        self.schedule_update_ha_state()


class APsystemsStorageControlPanelsModeSwitch(CoordinatorEntity, SwitchEntity):
    """Virtual parameter switch (state automatically syncs with device reported data)."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_controlpanels_mode_switch"
        # self._attr_name = "controlpanels_mode_switch"
        self._base_name = "controlpanels_mode_switch"
        self._attr_name = self._base_name
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

        # Variable to hold pending state before manual dispatch
        self._pending_state = None

    @property
    def name(self) -> str:
        """Return the name of the entity, appending a marker if there are pending changes."""
        if self._pending_state is not None:
            return f"{self._base_name} *"
        return self._base_name

    @property
    def is_on(self) -> bool:
        """Return the current control panel mode status from the coordinator's real-time data."""
        if self._pending_state is not None:
            return self._pending_state

        if self.coordinator.data is None:
            return False

        mode_state = self.coordinator.data.get("control-panels", {}).get("data", {}).get("mode")
        return mode_state == "1"

    async def async_turn_on(self, **kwargs) -> None:
        """Handle user turning on the switch in HA UI (stores locally without sending command)."""
        self._pending_state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Handle user turning off the switch in HA UI (stores locally without sending command)."""
        self._pending_state = False
        self.async_write_ha_state()

    def clear_pending_data(self):
        """Clear the locally stored pending state."""
        self._pending_state = None
        # Use thread-safe state update method recommended by Home Assistant
        self.schedule_update_ha_state()