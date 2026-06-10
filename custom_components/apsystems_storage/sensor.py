"""APsystems Storage sensor platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL, SENSOR_CONFIGS
from .coordinator import APsystemsStorageCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up APsystems Storage sensors from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.
        async_add_entities: Callback to add entities.

    """
    coordinator: APsystemsStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for config in SENSOR_CONFIGS:
        description = SensorEntityDescription(
            key=f"{config['endpoint']}_{config['key']}",
            translation_key=str(config["translation_key"]) if config.get("translation_key") else None,
            name=str(config["name"]),
            device_class=config.get("device_class"),
            state_class=config.get("state_class"),
            entity_category=config.get("entity_category"),
            native_unit_of_measurement=config.get("native_unit"),
            entity_registry_enabled_default=not config.get("disabled_by_default", False),
        )
        entities.append(
            APsystemsStorageSensor(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                description=description,
                endpoint=str(config["endpoint"]),
                json_key=str(config["key"]),
            )
        )

    async_add_entities(entities)


class APsystemsStorageSensor(CoordinatorEntity[APsystemsStorageCoordinator], SensorEntity):
    """Represents an APsystems Storage sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
        description: SensorEntityDescription,
        endpoint: str,
        json_key: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.
            description: The sensor entity description.
            endpoint: The API endpoint this sensor reads from.
            json_key: The JSON key path to extract from the endpoint data.

        """
        super().__init__(coordinator)
        self.entity_description = description
        self._endpoint = endpoint
        self._json_key = json_key
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{endpoint}_{json_key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
            # "model": MODEL,
        }

    @property
    def available(self) -> bool:
        """Return True if the entity is available."""
        return (
            self.coordinator.data is not None
            and self.coordinator.last_update_success
        )

    @property
    def native_value(self) -> str | float | int | None:
        """Return the current value of the sensor.

        Supports nested key extraction using dot notation (e.g., "data.temperature").

        Returns:
            The extracted value, or None if the path is invalid.

        """
        data = self.coordinator.data.get(self._endpoint)
        if data is None:
            return None

        if self._json_key:
            if isinstance(data, dict):
                if "." in self._json_key:
                    keys = self._json_key.split(".")
                    temp_data: Any = data
                    try:
                        for k in keys:
                            temp_data = temp_data[k]
                        return temp_data
                    except (KeyError, TypeError):
                        return None
                else:
                    return data.get(self._json_key)
            return None

        return str(data)
