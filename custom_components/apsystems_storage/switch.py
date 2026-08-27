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
from .coordinator import APsystemsStorageCoordinator, endpoint_field

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

    eco_switch = APsystemsStorageEcoSwitch(
        coordinator=coordinator, entry_id=entry.entry_id
    )
    offgrid_on_switch = APsystemsStorageOffgridOnSwitch(
        coordinator=coordinator, entry_id=entry.entry_id
    )
    control_panels_mode_switch = APsystemsStorageControlPanelsModeSwitch(
        coordinator=coordinator, entry_id=entry.entry_id
    )

    # Register on the coordinator so the settings buttons can read the staged
    # values of *this* config entry without going through the state machine.
    coordinator.modes_eco_switch_entity = eco_switch
    coordinator.modes_offgrid_on_switch_entity = offgrid_on_switch
    coordinator.controlpanels_mode_switch_entity = control_panels_mode_switch

    async_add_entities([eco_switch, offgrid_on_switch, control_panels_mode_switch])


class APsystemsStorageStagedSwitch(
    CoordinatorEntity[APsystemsStorageCoordinator], SwitchEntity
):
    """Base class for switches that stage the user's edit until it is dispatched.

    Toggling the switch does not talk to the device; the value is kept locally
    until the matching "Confirm ..." button posts it.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
        description: SwitchEntityDescription,
        endpoint: str,
        field: str,
    ) -> None:
        """Initialize the staged switch.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.
            description: The switch entity description.
            endpoint: The API endpoint holding this switch's value.
            field: The field name inside the endpoint payload.

        """
        super().__init__(coordinator)
        self.entity_description = description
        self._endpoint = endpoint
        self._field = field
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
        }
        self._pending_state: bool | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes.

        The base name comes from ``entity_description.name``. Returning ``None``
        here would cause Home Assistant (because ``_attr_has_entity_name`` is
        True) to display only the device name and hide the switch's own label
        (e.g. "Eco Mode"). We always return a real name so the UI shows
        ``"APsystems Storage Eco Mode"`` (with ``" *"`` while a change is
        staged).
        """
        if self._pending_state is not None:
            return f"{self.entity_description.name} *"
        return self.entity_description.name

    @property
    def is_on(self) -> bool:
        """Return the staged value, or the device value from the coordinator."""
        if self._pending_state is not None:
            return self._pending_state

        return str(endpoint_field(self.coordinator, self._endpoint, self._field)) == "1"

    @property
    def staged_api_value(self) -> str | None:
        """Return the value to post to the device, or None if unknown."""
        if self._pending_state is not None:
            return "1" if self._pending_state else "0"

        raw_value = endpoint_field(self.coordinator, self._endpoint, self._field)
        if raw_value is None:
            return None

        return "1" if str(raw_value) == "1" else "0"

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


class APsystemsStorageEcoSwitch(APsystemsStorageStagedSwitch):
    """Switch entity for the Eco mode setting."""

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
        super().__init__(
            coordinator,
            entry_id,
            SwitchEntityDescription(
                key="modes_eco_switch",
                translation_key="eco_mode",
                name="Eco Mode",
                entity_category=EntityCategory.CONFIG,
            ),
            endpoint="modes",
            field="eco",
        )


class APsystemsStorageOffgridOnSwitch(APsystemsStorageStagedSwitch):
    """Switch entity for the Off-grid On setting."""

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
        super().__init__(
            coordinator,
            entry_id,
            SwitchEntityDescription(
                key="modes_offgrid_on_switch",
                translation_key="off_grid_on_hold",
                name="Off-grid On Hold",
                entity_category=EntityCategory.CONFIG,
            ),
            endpoint="modes",
            field="offgrid_on",
        )


class APsystemsStorageControlPanelsModeSwitch(APsystemsStorageStagedSwitch):
    """Switch entity for the Control Panels mode setting."""

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
        super().__init__(
            coordinator,
            entry_id,
            SwitchEntityDescription(
                key="controlpanels_mode_switch",
                translation_key="control_panel_mode",
                name="Control Panel Mode",
                entity_category=EntityCategory.CONFIG,
            ),
            endpoint="control-panels",
            field="mode",
        )
