"""APsystems Storage DataUpdate Coordinator."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Protocol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .apsystems_api import APsystemsStorageApiClient, APsystemsStorageApiError
from .const import (
    DEFAULT_SCAN_INTERVAL,
    GET_ENDPOINTS,
    POLLED_ENDPOINTS,
    STATIC_ENDPOINTS,
)

_LOGGER = logging.getLogger(__name__)


def endpoint_field(
    coordinator: APsystemsStorageCoordinator, endpoint: str, field: str
) -> Any | None:
    """Return a single field from an endpoint payload, or None if unavailable.

    The API client stores ``None`` for endpoints that failed to fetch, so every
    level has to be guarded before it is indexed.

    Args:
        coordinator: The data coordinator holding the last fetched data.
        endpoint: The API endpoint key, e.g. ``modes``.
        field: The field name inside the endpoint's ``data`` object.

    Returns:
        The field value, or None when the data is not available.

    """
    data = coordinator.data
    if not data:
        return None

    endpoint_data = data.get(endpoint)
    if not isinstance(endpoint_data, dict):
        return None

    payload = endpoint_data.get("data")
    if not isinstance(payload, dict):
        return None

    return payload.get(field)


class StagedEntity(Protocol):
    """An entity that stages a user edit locally until a button dispatches it.

    The "Confirm ..." buttons collect the staged values from these entities.
    They are handed out by the coordinator, which is created per config entry,
    so a second inverter can never receive another device's values.
    """

    @property
    def staged_api_value(self) -> Any | None:
        """Return the value to post to the device, or None if unknown."""

    def clear_pending_data(self) -> None:
        """Discard the locally staged value."""


class APsystemsStorageCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for polling APsystems Storage device data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: APsystemsStorageApiClient,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: The Home Assistant instance.
            api_client: The API client for device communication.
            scan_interval: Polling interval in seconds.

        """
        super().__init__(
            hass,
            _LOGGER,
            name="APsystems Storage Device",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api_client = api_client

        # Static device identity data is fetched once and reused afterwards so
        # that each polling cycle only hits the live endpoints.
        self._static_data: dict[str, Any] = {}

        # Entities that stage user edits until a "Confirm ..." button posts
        # them. Registered by the platforms during setup; scoped to this config
        # entry, which is why the buttons read from here instead of resolving
        # hardcoded entity IDs through the state machine.
        self.modes_eco_switch_entity: StagedEntity | None = None
        self.modes_offgrid_on_switch_entity: StagedEntity | None = None
        self.modes_mode_select_entity: StagedEntity | None = None
        self.modes_dod_number_entity: StagedEntity | None = None
        self.modes_backup_charge_power_number_entity: StagedEntity | None = None
        self.modes_time_config_text_entity: StagedEntity | None = None
        self.controlpanels_mode_switch_entity: StagedEntity | None = None
        self.controlpanels_config_text_entity: StagedEntity | None = None

    @property
    def modes_staged_entities(self) -> dict[str, StagedEntity | None]:
        """Return the *modes* payload fields mapped to their staging entities."""
        return {
            "eco": self.modes_eco_switch_entity,
            "offgrid_on": self.modes_offgrid_on_switch_entity,
            "mode": self.modes_mode_select_entity,
            "dod": self.modes_dod_number_entity,
            "backup_charP": self.modes_backup_charge_power_number_entity,
            "time_cfg": self.modes_time_config_text_entity,
        }

    @property
    def controlpanels_staged_entities(self) -> dict[str, StagedEntity | None]:
        """Return the *control-panels* payload fields mapped to their entities."""
        return {
            "mode": self.controlpanels_mode_switch_entity,
            "MI1": self.controlpanels_config_text_entity,
        }

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device API.

        Only the live endpoints are polled on every cycle. The static *devices*
        endpoint is fetched once and then served from cache, which keeps the
        request rate at the inverter down.

        Returns:
            A dictionary mapping endpoint names to their JSON response data.

        Raises:
            UpdateFailed: If the data fetch fails.

        """
        try:
            if not self._static_data:
                data = await self.api_client.async_get_data(GET_ENDPOINTS)
                self._static_data = {
                    endpoint: data[endpoint]
                    for endpoint in STATIC_ENDPOINTS
                    if data.get(endpoint) is not None
                }
                return data

            data = await self.api_client.async_get_data(POLLED_ENDPOINTS)
        except APsystemsStorageApiError as err:
            raise UpdateFailed(f"Failed to fetch data: {err}") from err

        return {**self._static_data, **data}

    async def async_request_refresh_now(self) -> None:
        """Request an immediate data refresh from the device."""
        _LOGGER.debug("Requesting immediate data refresh")
        await self.async_request_refresh()
