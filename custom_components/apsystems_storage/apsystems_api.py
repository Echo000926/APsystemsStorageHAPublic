"""APsystems Storage API client."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import GET_ENDPOINTS

_LOGGER = logging.getLogger(__name__)

# Default request timeout in seconds
DEFAULT_TIMEOUT = 10


class APsystemsStorageApiError(Exception):
    """Exception raised when an API request fails."""


class APsystemsStorageApiClient:
    """Client for communicating with the APsystems Storage device API."""

    def __init__(
        self,
        host: str,
        port: int | str,
        session: aiohttp.ClientSession,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the API client.

        Args:
            host: The IP address or hostname of the device.
            port: The port number of the device API.
            session: An aiohttp client session.
            timeout: Request timeout in seconds.

        """
        self._host = host
        self._port = port
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._base_url = f"http://{self._host}:{self._port}"

    @property
    def base_url(self) -> str:
        """Return the base URL of the device API."""
        return self._base_url

    async def async_test_connection(self) -> bool:
        """Test if the device is reachable.

        Returns:
            True if the device responds successfully.

        Raises:
            APsystemsStorageApiError: If the connection test fails.

        """
        try:
            async with self._session.get(
                f"{self._base_url}/devices",
                timeout=self._timeout,
            ) as response:
                if response.status == 200:
                    return True
                raise APsystemsStorageApiError(
                    f"Device returned HTTP status {response.status}"
                )
        except aiohttp.ClientError as err:
            raise APsystemsStorageApiError(
                f"Failed to connect to device at {self._host}:{self._port} -- {self._base_url}: {err}"
            ) from err
        except asyncio.TimeoutError as err:
            raise APsystemsStorageApiError(
                f"Connection timed out for device at {self._base_url}"
            ) from err

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch data from all configured GET endpoints.

        Returns:
            A dictionary mapping endpoint names to their JSON response data.

        Raises:
            APsystemsStorageApiError: If no data could be fetched from any endpoint.

        """
        data: dict[str, Any] = {}
        for endpoint in GET_ENDPOINTS:
            url = f"{self._base_url}/{endpoint}"
            try:
                async with self._session.get(
                    url, timeout=self._timeout
                ) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        data[endpoint] = json_data
                        _LOGGER.debug("Successfully fetched [%s]: %s", endpoint, json_data)
                    else:
                        _LOGGER.warning(
                            "Failed to fetch %s, HTTP status code: %s", url, response.status
                        )
                        data[endpoint] = None
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                _LOGGER.error("Network error while requesting %s: %s", url, err)
                data[endpoint] = None
            except Exception as err:
                _LOGGER.error("Unexpected error while requesting %s: %s", url, err)
                data[endpoint] = None

        if not any(v is not None for v in data.values()):
            raise APsystemsStorageApiError(
                "Failed to fetch data from any endpoint."
            )

        return data

    async def async_post_data(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a POST request to the device API.

        Args:
            endpoint: The API endpoint to post to.
            payload: The JSON payload to send.

        Returns:
            The JSON response from the device.

        Raises:
            APsystemsStorageApiError: If the request fails.

        """
        url = f"{self._base_url}/{endpoint}"
        try:
            async with self._session.post(
                url, json=payload, timeout=self._timeout
            ) as response:
                if response.status == 200:
                    try:
                        json_data = await response.json()
                    except Exception:
                        json_data = {}
                    return json_data
                error_text = await response.text()
                raise APsystemsStorageApiError(
                    f"POST {url} failed with HTTP status {response.status}: {error_text}"
                )
        except aiohttp.ClientError as err:
            raise APsystemsStorageApiError(
                f"Network error during POST {url}: {err}"
            ) from err
        except asyncio.TimeoutError as err:
            raise APsystemsStorageApiError(
                f"Request timed out during POST {url}"
            ) from err
