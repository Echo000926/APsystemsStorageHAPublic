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
from .coordinator import APsystemsStorageCoordinator, endpoint_field

_LOGGER = logging.getLogger(__name__)

# Mapping for operating mode snake_case option keys to actual device values
MODES_OPERATING_MODE_MAP = {
    "ai_mode": "1",
    "self_consumption_mode": "2",
    "time_of_use_mode": "3",
    "backup_mode": "4",
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

    mode_select = APsystemsStorageModesModeSelect(
        coordinator=coordinator, entry_id=entry.entry_id
    )

    # Register on the coordinator so the settings buttons can read the staged
    # values of *this* config entry without going through the state machine.
    coordinator.modes_mode_select_entity = mode_select

    async_add_entities([mode_select])


class APsystemsStorageStagedSelect(
    CoordinatorEntity[APsystemsStorageCoordinator], SelectEntity
):
    """Base class for selects that stage the user's choice until it is dispatched.

    Picking an option does not talk to the device; the value is kept locally
    until the matching "Confirm ..." button posts it.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
        description: SelectEntityDescription,
        unique_id_suffix: str,
        endpoint: str,
        field: str,
        option_to_value: dict[str, str],
    ) -> None:
        """Initialize the staged select.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.
            description: The select entity description.
            unique_id_suffix: Suffix for the entity's unique ID.
            endpoint: The API endpoint holding this select's value.
            field: The field name inside the endpoint payload.
            option_to_value: Mapping of option keys to device values.

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

        # Options use snake_case keys; HA translates them via translations/
        self._option_to_value_map = option_to_value
        self._value_to_option_map = {v: k for k, v in option_to_value.items()}
        self._pending_option: str | None = None

    @property
    def name(self) -> str | None:
        """Return the name, appending a marker if there are pending changes.

        Returning ``None`` here would let Home Assistant fall back to the
        device name alone (because ``_attr_has_entity_name`` is True), which
        would hide the select's own label such as "Operating Mode". We always
        return a real name from ``entity_description.name`` so the UI shows
        ``"APsystems Storage Operating Mode"`` (with ``" *"`` while a change
        is staged).
        """
        if self._pending_option is not None:
            return f"{self.entity_description.name} *"
        return self.entity_description.name

    @property
    def options(self) -> list[str]:
        """Return the available options."""
        return list(self._option_to_value_map)

    @property
    def current_option(self) -> str | None:
        """Return the staged option, or the device value from the coordinator."""
        if self._pending_option is not None:
            return self._pending_option

        raw_value = endpoint_field(self.coordinator, self._endpoint, self._field)
        if raw_value is None:
            return None

        return self._value_to_option_map.get(str(raw_value))

    @property
    def staged_api_value(self) -> str | None:
        """Return the value to post to the device, or None if unknown."""
        option = self.current_option
        if option is None:
            return None

        return self._option_to_value_map.get(option)

    async def async_select_option(self, option: str) -> None:
        """Handle user selection of an option in the HA UI."""
        _LOGGER.debug("User selected %s: %s", self.entity_description.key, option)
        self._pending_option = option
        self.async_write_ha_state()

    def clear_pending_data(self) -> None:
        """Clear the locally stored pending option."""
        self._pending_option = None
        self.schedule_update_ha_state()


class APsystemsStorageModesModeSelect(APsystemsStorageStagedSelect):
    """Select entity for operating modes."""

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
        super().__init__(
            coordinator,
            entry_id,
            SelectEntityDescription(
                key="modes_operating_mode",
                translation_key="operating_mode",
                name="Operating Mode",
                entity_category=EntityCategory.CONFIG,
            ),
            unique_id_suffix="modes_mode_select",
            endpoint="modes",
            field="mode",
            option_to_value=MODES_OPERATING_MODE_MAP,
        )
