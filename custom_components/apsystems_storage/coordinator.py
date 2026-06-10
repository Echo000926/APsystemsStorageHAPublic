"""APsystems Storage DataUpdate Coordinator."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .apsystems_api import APsystemsStorageApiClient, APsystemsStorageApiError

_LOGGER = logging.getLogger(__name__)

# Default polling interval in seconds
UPDATE_INTERVAL_SECONDS = 10


class APsystemsStorageCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for polling APsystems Storage device data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: APsystemsStorageApiClient,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: The Home Assistant instance.
            api_client: The API client for device communication.

        """
        super().__init__(
            hass,
            _LOGGER,
            name="APsystems Storage Device",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.api_client = api_client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device API.

        Returns:
            A dictionary mapping endpoint names to their JSON response data.

        Raises:
            UpdateFailed: If the data fetch fails.

        """
        try:
            return await self.api_client.async_get_data()
        except APsystemsStorageApiError as err:
            raise UpdateFailed(f"Failed to fetch data: {err}") from err

    async def async_request_refresh_now(self) -> None:
        """Request an immediate data refresh from the device."""
        _LOGGER.debug("Requesting immediate data refresh")
        await self.async_request_refresh()
