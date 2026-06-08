"""ApsystemsStorage modes DoD number platform."""
import logging
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the DoD number entity via config flow."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Instantiate the DoD number entity and attach it to the coordinator
    modes_dod_number = APsystemsStorageModesDODNumber(coordinator, entry)
    coordinator.modes_dod_number_entity = modes_dod_number

    modes_backup_charge_power_number = APsystemsStorageModesBackupChargePowerNumber(coordinator, entry)
    coordinator.modes_backup_charge_power_number_entity = modes_backup_charge_power_number

    entities = [modes_dod_number, modes_backup_charge_power_number]
    async_add_entities(entities)


class APsystemsStorageModesDODNumber(CoordinatorEntity, NumberEntity):
    """Represents a number entity for Depth of Discharge (DoD) settings."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_modes_dod"
        # self._attr_name = "modes_dod"
        self._base_name = "modes_dod"
        self._attr_name = self._base_name
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

        # Configure min/max limits and step
        self._attr_native_min_value = 15
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_mode = NumberMode.BOX

        # Variable to hold pending value before manual dispatch
        self._pending_dod_number = None

    @property
    def name(self) -> str:
        """Return the name of the entity, appending a marker if there are pending changes."""
        if self._pending_dod_number is not None:
            return f"{self._base_name} *"
        return self._base_name

    @property
    def native_value(self) -> float | None:
        """Return the current DoD value from the coordinator or pending state."""
        if self._pending_dod_number is not None:
            return self._pending_dod_number

        if self.coordinator.data is None:
            return None

        dod_value = self.coordinator.data.get("modes", {}).get("data", {}).get("dod")

        if dod_value is None:
            return None

        _LOGGER.debug("Current DoD value fetched from coordinator: %s", dod_value)
        return int(dod_value)

    async def async_set_native_value(self, value: float) -> None:
        """Handle user input when modifying the number in HA UI."""
        _LOGGER.debug("User set DoD value to: %s", value)

        # Temporarily store the new value locally
        self._pending_dod_number = value
        self.async_write_ha_state()

    def clear_pending_data(self):
        """Clear the locally stored pending DoD value."""
        self._pending_dod_number = None
        # Use thread-safe state update method recommended by Home Assistant
        self.schedule_update_ha_state()


class APsystemsStorageModesBackupChargePowerNumber(CoordinatorEntity, NumberEntity):
    """Represents a number entity for backup mode charge power settings."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_modes_backup_charge_power"
        # self._attr_name = "modes_dod"
        self._base_name = "modes_backup_charge_power"
        self._attr_name = self._base_name
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

        # Configure min/max limits and step
        self._attr_native_min_value = 0
        self._attr_native_max_value = 2500
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "W"
        self._attr_mode = NumberMode.BOX

        # Variable to hold pending value before manual dispatch
        self._pending_number = None

    @property
    def name(self) -> str:
        """Return the name of the entity, appending a marker if there are pending changes."""
        if self._pending_number is not None:
            return f"{self._base_name} *"
        return self._base_name

    @property
    def native_value(self) -> float | None:
        """Return the current backup_charP value from the coordinator or pending state."""
        if self._pending_number is not None:
            return self._pending_number

        if self.coordinator.data is None:
            return None

        power_value = self.coordinator.data.get("modes", {}).get("data", {}).get("backup_charP")

        if power_value is None:
            return None

        _LOGGER.debug("Current backup_charP value fetched from coordinator: %s", power_value)
        return int(power_value)

    async def async_set_native_value(self, value: float) -> None:
        """Handle user input when modifying the number in HA UI."""
        _LOGGER.debug("User set backup_charP value to: %s", value)

        # Temporarily store the new value locally
        self._pending_number = value
        self.async_write_ha_state()

    def clear_pending_data(self):
        """Clear the locally stored pending DoD value."""
        self._pending_number = None
        # Use thread-safe state update method recommended by Home Assistant
        self.schedule_update_ha_state()