"""APsystems Storage number platform."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
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
    """Set up APsystems Storage number entities from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.
        async_add_entities: Callback to add entities.

    """
    coordinator: APsystemsStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        APsystemsStorageModesDODNumber(coordinator=coordinator, entry_id=entry.entry_id),
        APsystemsStorageModesBackupChargePowerNumber(
            coordinator=coordinator, entry_id=entry.entry_id
        ),
    ]

    # Attach entities to coordinator for later pending state management
    coordinator.modes_dod_number_entity = entities[0]
    coordinator.modes_backup_charge_power_number_entity = entities[1]

    async_add_entities(entities)


class APsystemsStorageModesDODNumber(
    CoordinatorEntity[APsystemsStorageCoordinator], NumberEntity
):
    """Number entity for Depth of Discharge (DoD) settings."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the DoD number entity.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = NumberEntityDescription(
            key="modes_dod",
            translation_key="depth_of_discharge",
            name="Depth of Discharge",
            native_min_value=15,
            native_max_value=100,
            native_step=1,
            native_unit_of_measurement="%",
            mode=NumberMode.BOX,
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_modes_dod"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }
        self._pending_dod_number: float | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes."""
        if self._pending_dod_number is not None:
            return f"{self.entity_description.name} *"
        return None  # Let HA use translation_key from entity description

    @property
    def native_value(self) -> float | None:
        """Return the current DoD value from the coordinator or pending state."""
        if self._pending_dod_number is not None:
            return self._pending_dod_number

        if self.coordinator.data is None:
            return None

        dod_value = (
            self.coordinator.data.get("modes", {}).get("data", {}).get("dod")
        )
        if dod_value is None:
            return None

        _LOGGER.debug("Current DoD value fetched from coordinator: %s", dod_value)
        try:
            return int(dod_value)
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Handle user input when modifying the number in HA UI."""
        _LOGGER.debug("User set DoD value to: %s", value)
        self._pending_dod_number = value
        self.async_write_ha_state()

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending DoD value."""
        self._pending_dod_number = None
        self.schedule_update_ha_state()


class APsystemsStorageModesBackupChargePowerNumber(
    CoordinatorEntity[APsystemsStorageCoordinator], NumberEntity
):
    """Number entity for backup mode charge power settings."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the backup charge power number entity.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(coordinator)
        self.entity_description = NumberEntityDescription(
            key="modes_backup_charge_power",
            translation_key="backup_charge_power",
            name="Backup Charge Power",
            native_min_value=0,
            native_max_value=2500,
            native_step=1,
            native_unit_of_measurement="W",
            mode=NumberMode.BOX,
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_modes_backup_charge_power"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }
        self._pending_number: float | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes."""
        if self._pending_number is not None:
            return f"{self.entity_description.name} *"
        return None  # Let HA use translation_key from entity description

    @property
    def native_value(self) -> float | None:
        """Return the current backup_charP value from the coordinator or pending state."""
        if self._pending_number is not None:
            return self._pending_number

        if self.coordinator.data is None:
            return None

        power_value = (
            self.coordinator.data.get("modes", {}).get("data", {}).get("backup_charP")
        )
        if power_value is None:
            return None

        _LOGGER.debug("Current backup_charP value fetched from coordinator: %s", power_value)
        try:
            return int(power_value)
        except (ValueError, TypeError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Handle user input when modifying the number in HA UI."""
        _LOGGER.debug("User set backup_charP value to: %s", value)
        self._pending_number = value
        self.async_write_ha_state()

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending value."""
        self._pending_number = None
        self.schedule_update_ha_state()
