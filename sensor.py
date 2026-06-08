"""ApsystemsStorage sensor platform."""
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, SENSOR_CONFIGS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensors via config flow."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    # Iterate through the configuration list to dynamically generate entities
    for config in SENSOR_CONFIGS:
        entities.append(APsystemsStorageSensor(coordinator, config, entry.entry_id))

    async_add_entities(entities)


class APsystemsStorageSensor(CoordinatorEntity, SensorEntity):
    """Represents an APsystemsStorage sensor entity."""

    def __init__(self, coordinator, config, entry_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.endpoint = config["endpoint"]
        self.json_key = config.get("key")  # Get the specific field name to parse
        self.entry_id = entry_id

        # Dynamically generate unique ID and name
        key_suffix = self.json_key if self.json_key else "raw"
        self._attr_unique_id = f"APsystemsStorage_{entry_id}_{self.endpoint}_{key_suffix}"
        self._attr_name = f"{self.endpoint}_{config['name']}"

        # Device registry information
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "APsystemsStorage Device",
            "manufacturer": "APsystems",
        }

    @property
    def available(self) -> bool:
        """Return True if the entity is available."""
        # Entity becomes unavailable (grayed out) if coordinator data is missing
        # or if the last update failed (e.g., UpdateFailed exception was raised).
        return self.coordinator.data is not None and self.coordinator.last_update_success

    @property
    def native_value(self):
        """Return the current value of the sensor."""
        data = self.coordinator.data.get(self.endpoint)

        if data is None:
            return None

        # If a specific key is configured, extract it precisely
        if self.json_key:
            if isinstance(data, dict):
                # Support nested key extraction like "data.temperature"
                if "." in self.json_key:
                    keys = self.json_key.split(".")
                    temp_data = data
                    try:
                        for k in keys:
                            # Traverse deeper into the dictionary
                            temp_data = temp_data[k]
                        return temp_data
                    except (KeyError, TypeError):
                        # Return None if the path is invalid or intermediate layer is not a dict
                        return None
                else:
                    # Direct key extraction logic
                    return data.get(self.json_key)
            return None

        # If no key is configured, return the raw JSON data as a string
        return str(data)