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
from .coordinator import APsystemsStorageCoordinator, endpoint_field

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

    dod_number = APsystemsStorageModesDODNumber(
        coordinator=coordinator, entry_id=entry.entry_id
    )
    backup_charge_power_number = APsystemsStorageModesBackupChargePowerNumber(
        coordinator=coordinator, entry_id=entry.entry_id
    )

    # Register on the coordinator so the settings buttons can read the staged
    # values of *this* config entry without going through the state machine.
    coordinator.modes_dod_number_entity = dod_number
    coordinator.modes_backup_charge_power_number_entity = backup_charge_power_number

    async_add_entities([dod_number, backup_charge_power_number])


class APsystemsStorageStagedNumber(
    CoordinatorEntity[APsystemsStorageCoordinator], NumberEntity
):
    """Base class for numbers that stage the user's input until it is dispatched.

    Changing the value does not talk to the device; it is kept locally until the
    matching "Confirm ..." button posts it.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
        description: NumberEntityDescription,
        unique_id_suffix: str,
        endpoint: str,
        field: str,
    ) -> None:
        """Initialize the staged number entity.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.
            description: The number entity description.
            unique_id_suffix: Suffix for the entity's unique ID.
            endpoint: The API endpoint holding this number's value.
            field: The field name inside the endpoint payload.

        """
        super().__init__(coordinator)
        self.entity_description = description
        self._endpoint = endpoint
        self._field = field
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{unique_id_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
        }
        self._pending_value: float | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes.

        Returning ``None`` here would let Home Assistant fall back to the
        device name alone (because ``_attr_has_entity_name`` is True), which
        would hide the number's own label such as "Depth of Discharge". We
        always return a real name from ``entity_description.name`` so the UI
        shows ``"APsystems Storage Depth of Discharge"`` (with ``" *"`` while
        a change is staged).
        """
        if self._pending_value is not None:
            return f"{self.entity_description.name} *"
        return self.entity_description.name

    @property
    def native_value(self) -> float | None:
        """Return the staged value, or the device value from the coordinator."""
        if self._pending_value is not None:
            return self._pending_value

        raw_value = endpoint_field(self.coordinator, self._endpoint, self._field)
        if raw_value is None:
            return None

        try:
            return int(raw_value)
        except (ValueError, TypeError):
            return None

    @property
    def staged_api_value(self) -> str | None:
        """Return the value to post to the device, or None if unknown."""
        value = self.native_value
        if value is None:
            return None

        return str(int(value))

    async def async_set_native_value(self, value: float) -> None:
        """Handle user input when modifying the number in HA UI."""
        _LOGGER.debug("User set %s to: %s", self.entity_description.key, value)
        self._pending_value = value
        self.async_write_ha_state()

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending value."""
        self._pending_value = None
        self.schedule_update_ha_state()


class APsystemsStorageModesDODNumber(APsystemsStorageStagedNumber):
    """Number entity for Depth of Discharge (DoD) settings."""

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
        super().__init__(
            coordinator,
            entry_id,
            NumberEntityDescription(
                key="modes_dod",
                translation_key="depth_of_discharge",
                name="Depth of Discharge",
                native_min_value=15,
                native_max_value=100,
                native_step=1,
                native_unit_of_measurement="%",
                mode=NumberMode.BOX,
                entity_category=EntityCategory.CONFIG,
            ),
            unique_id_suffix="modes_dod",
            endpoint="modes",
            field="dod",
        )


class APsystemsStorageModesBackupChargePowerNumber(APsystemsStorageStagedNumber):
    """Number entity for backup mode charge power settings."""

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
        super().__init__(
            coordinator,
            entry_id,
            NumberEntityDescription(
                key="modes_backup_charge_power",
                translation_key="backup_charge_power",
                name="Backup Charge Power",
                native_min_value=0,
                native_max_value=2500,
                native_step=1,
                native_unit_of_measurement="W",
                mode=NumberMode.BOX,
                entity_category=EntityCategory.CONFIG,
            ),
            unique_id_suffix="modes_backup_charge_power",
            endpoint="modes",
            field="backup_charP",
        )
