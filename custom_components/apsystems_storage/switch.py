"""APsystems Storage switch platform."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
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
    """Set up APsystems Storage switch entities from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.
        async_add_entities: Callback to add entities.

    """
    coordinator: APsystemsStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        APsystemsStorageEcoSwitch(coordinator=coordinator, entry_id=entry.entry_id),
        APsystemsStorageOffgridOnSwitch(coordinator=coordinator, entry_id=entry.entry_id),
        APsystemsStorageControlPanelsModeSwitch(coordinator=coordinator, entry_id=entry.entry_id),
    ]

    # Attach entities to coordinator for later pending state management
    coordinator.modes_eco_switch_entity = entities[0]
    coordinator.modes_offgrid_on_switch_entity = entities[1]
    coordinator.controlpanels_mode_switch_entity = entities[2]

    async_add_entities(entities)


class APsystemsStorageEcoSwitch(CoordinatorEntity[APsystemsStorageCoordinator], SwitchEntity):
    """Switch entity for the Eco mode setting."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the Eco switch.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = SwitchEntityDescription(
            key="modes_eco_switch",
            translation_key="eco_mode",
            name="Eco Mode",
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_modes_eco_switch"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }
        self._pending_state: bool | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes."""
        if self._pending_state is not None:
            return f"{self.entity_description.name} *"
        return f"{self.entity_description.name}"

    @property
    def is_on(self) -> bool:
        """Return the current eco status from the coordinator's real-time data."""
        if self._pending_state is not None:
            return self._pending_state

        if self.coordinator.data is None:
            return False

        eco_status = (
            self.coordinator.data.get("modes", {}).get("data", {}).get("eco")
        )
        return eco_status == "1"

    async def async_turn_on(self, **kwargs: object) -> None:
        """Handle user turning on the switch (stores locally without sending command)."""
        self._pending_state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Handle user turning off the switch (stores locally without sending command)."""
        self._pending_state = False
        self.async_write_ha_state()

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending state."""
        self._pending_state = None
        self.schedule_update_ha_state()


class APsystemsStorageOffgridOnSwitch(CoordinatorEntity[APsystemsStorageCoordinator], SwitchEntity):
    """Switch entity for the Off-grid On setting."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the Off-grid On switch.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = SwitchEntityDescription(
            key="modes_offgrid_on_switch",
            translation_key="off_grid_on_hold",
            name="Off-grid On Hold",
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_modes_offgrid_on_switch"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }
        self._pending_state: bool | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes."""
        if self._pending_state is not None:
            return f"{self.entity_description.name} *"
        return f"{self.entity_description.name}"

    @property
    def is_on(self) -> bool:
        """Return the current offgrid-on status from the coordinator's real-time data."""
        if self._pending_state is not None:
            return self._pending_state

        if self.coordinator.data is None:
            return False

        offgrid_on_status = (
            self.coordinator.data.get("modes", {}).get("data", {}).get("offgrid_on")
        )
        return offgrid_on_status == "1"

    async def async_turn_on(self, **kwargs: object) -> None:
        """Handle user turning on the switch (stores locally without sending command)."""
        self._pending_state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Handle user turning off the switch (stores locally without sending command)."""
        self._pending_state = False
        self.async_write_ha_state()

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending state."""
        self._pending_state = None
        self.schedule_update_ha_state()


class APsystemsStorageControlPanelsModeSwitch(
    CoordinatorEntity[APsystemsStorageCoordinator], SwitchEntity
):
    """Switch entity for the Control Panels mode setting."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the Control Panels mode switch.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = SwitchEntityDescription(
            key="controlpanels_mode_switch",
            translation_key="control_panel_mode",
            name="Control Panel Mode",
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_controlpanels_mode_switch"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }
        self._pending_state: bool | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes."""
        if self._pending_state is not None:
            return f"{self.entity_description.name} *"
        return f"{self.entity_description.name}"

    @property
    def is_on(self) -> bool:
        """Return the current control panel mode status from the coordinator's real-time data."""
        if self._pending_state is not None:
            return self._pending_state

        if self.coordinator.data is None:
            return False

        mode_state = (
            self.coordinator.data.get("control-panels", {}).get("data", {}).get("mode")
        )
        return mode_state == "1"

    async def async_turn_on(self, **kwargs: object) -> None:
        """Handle user turning on the switch (stores locally without sending command)."""
        self._pending_state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Handle user turning off the switch (stores locally without sending command)."""
        self._pending_state = False
        self.async_write_ha_state()

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending state."""
        self._pending_state = None
        self.schedule_update_ha_state()
