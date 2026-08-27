"""APsystems Storage button platform."""
from __future__ import annotations

import copy
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .apsystems_api import APsystemsStorageApiError
from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import APsystemsStorageCoordinator, StagedEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up APsystems Storage button entities from a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.
        async_add_entities: Callback to add entities.

    """
    coordinator: APsystemsStorageCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        APsystemsStorageModesSettingsButton(
            coordinator=coordinator, entry_id=entry.entry_id
        ),
        APsystemsStorageControlPanelsSettingsButton(
            coordinator=coordinator, entry_id=entry.entry_id
        ),
    ]

    async_add_entities(entities)
    _LOGGER.debug(
        "Registered %d button entities for APsystems Storage", len(entities)
    )


class APsystemsStorageSettingsButton(
    CoordinatorEntity[APsystemsStorageCoordinator], ButtonEntity
):
    """Base class for buttons that dispatch staged settings to the device.

    The payload is assembled from the staging entities that belong to this
    config entry, which the coordinator hands out.  Entity IDs are deliberately
    not used: they are user-editable and not unique across devices, so a second
    inverter would otherwise get another device's staged values posted to it.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
        description: ButtonEntityDescription,
        endpoint: str,
        failure_translation_key: str,
        notification_title: str,
        notification_message: str,
        notification_id: str,
    ) -> None:
        """Initialize the settings button.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.
            description: The button entity description.
            endpoint: The API endpoint to post the payload to.
            failure_translation_key: Translation key raised when the device rejects.
            notification_title: Title of the success notification.
            notification_message: Body of the success notification.
            notification_id: ID of the success notification.

        """
        super().__init__(coordinator)
        self.entity_description = description
        self._entry_id = entry_id
        self._endpoint = endpoint
        self._failure_translation_key = failure_translation_key
        self._notification_title = notification_title
        self._notification_message = notification_message
        self._notification_id = notification_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": MODEL,
            "manufacturer": MANUFACTURER,
        }

    @property
    def _staged_entities(self) -> dict[str, StagedEntity | None]:
        """Return the payload fields mapped to their staging entities."""
        raise NotImplementedError

    def _build_payload(self) -> dict[str, Any]:
        """Collect the staged values of this config entry into a payload.

        Returns:
            The payload to post, containing only fields with a known value.

        """
        payload: dict[str, Any] = {}

        for field, entity in self._staged_entities.items():
            if entity is None:
                _LOGGER.debug("No entity registered yet for field %s", field)
                continue

            value = entity.staged_api_value
            if value is None:
                _LOGGER.debug("Skipping field %s, value is unknown", field)
                continue

            payload[field] = value

        return payload

    def _apply_optimistic_update(self, payload: dict[str, Any]) -> None:
        """Merge the posted payload into the coordinator data.

        Args:
            payload: The payload that was accepted by the device.

        """
        data = self.coordinator.data
        if not data:
            return

        new_data = copy.deepcopy(data)
        endpoint_data = new_data.get(self._endpoint)
        if not isinstance(endpoint_data, dict):
            return

        current = endpoint_data.get("data")
        if not isinstance(current, dict):
            return

        current.update(payload)
        self.coordinator.async_set_updated_data(new_data)
        _LOGGER.debug("Optimistically updated %s with %s", self._endpoint, payload)

    def _clear_staged_values(self) -> None:
        """Drop the staged values now that the device accepted them."""
        for entity in self._staged_entities.values():
            if entity is not None:
                entity.clear_pending_data()

    async def async_press(self) -> None:
        """Handle the button press from the frontend."""
        payload = self._build_payload()
        if not payload:
            _LOGGER.error("No values available to send to %s", self._endpoint)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="no_values_to_send",
            )

        _LOGGER.debug("Assembled payload for %s: %s", self._endpoint, payload)

        try:
            json_data = await self.coordinator.api_client.async_post_data(
                self._endpoint, payload
            )
        except APsystemsStorageApiError as err:
            # Staged values are kept, so the user can retry without re-entering.
            _LOGGER.error("Configuration request for %s failed: %s", self._endpoint, err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
                translation_placeholders={"error": str(err)},
            ) from err

        return_code = json_data.get("code", 201)
        if return_code != 200:
            _LOGGER.error(
                "Device rejected the %s configuration, returned code: %s",
                self._endpoint,
                return_code,
            )
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key=self._failure_translation_key,
            )

        _LOGGER.debug(
            "Configuration for %s sent successfully, device returned code: %s",
            self._endpoint,
            return_code,
        )

        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": self._notification_title,
                "message": self._notification_message,
                "notification_id": self._notification_id,
            },
        )

        self._apply_optimistic_update(payload)
        self._clear_staged_values()

        # Pull the real device state to replace the optimistic values.
        await self.coordinator.async_request_refresh_now()


class APsystemsStorageModesSettingsButton(APsystemsStorageSettingsButton):
    """Button entity to send unified mode settings to the device."""

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the modes settings button.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(
            coordinator,
            entry_id,
            ButtonEntityDescription(
                key="modes_settings_button",
                translation_key="confirm_modes_settings",
                name="Confirm Modes Settings",
                entity_category=EntityCategory.CONFIG,
            ),
            endpoint="modes",
            failure_translation_key="modes_config_failed",
            notification_title="Modes Configuration Result",
            notification_message=(
                "**Modes configuration has been successfully written to the device!**"
            ),
            notification_id="modes_config_feedback",
        )

    @property
    def _staged_entities(self) -> dict[str, StagedEntity | None]:
        """Return the *modes* payload fields mapped to their staging entities."""
        return self.coordinator.modes_staged_entities


class APsystemsStorageControlPanelsSettingsButton(APsystemsStorageSettingsButton):
    """Button entity to send unified control panel settings to the device."""

    def __init__(
        self,
        coordinator: APsystemsStorageCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the control panels settings button.

        Args:
            coordinator: The data coordinator.
            entry_id: The config entry ID.

        """
        super().__init__(
            coordinator,
            entry_id,
            ButtonEntityDescription(
                key="controlpanels_settings_button",
                translation_key="confirm_control_panels_settings",
                name="Confirm Control Panels Settings",
                entity_category=EntityCategory.CONFIG,
            ),
            endpoint="control-panels",
            failure_translation_key="control_panels_config_failed",
            notification_title="Control Panels Configuration Result",
            notification_message=(
                "**Control panels configuration has been successfully written "
                "to the device!**"
            ),
            notification_id="controlpanels_config_feedback",
        )

    @property
    def _staged_entities(self) -> dict[str, StagedEntity | None]:
        """Return the *control-panels* payload fields mapped to their entities."""
        return self.coordinator.controlpanels_staged_entities
