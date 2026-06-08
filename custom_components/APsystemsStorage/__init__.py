"""MyPlugin integration initialization."""
import logging
import asyncio
import aiohttp
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, GET_ENDPOINTS

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "select", "switch", "button", "number", "text"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MyPlugin from a config entry."""
    host = entry.data.get("host") or entry.data.get("ip")
    port = entry.data.get("port", 80)

    base_url = f"http://{host}:{port}"
    session = async_get_clientsession(hass)

    async def async_update_data():
        """Fetch data from all configured endpoints."""
        data = {}
        for endpoint in GET_ENDPOINTS:
            url = f"{base_url}/{endpoint}"
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        data[endpoint] = json_data
                        _LOGGER.debug("Successfully fetched [%s]: %s", endpoint, json_data)
                    else:
                        # Log warning but continue fetching other endpoints instead of raising immediately
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

        # If absolutely no data could be fetched, raise UpdateFailed to trigger coordinator retry
        if not any(v is not None for v in data.values()):
            raise UpdateFailed("Failed to fetch data from any endpoint.")

        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Device Data",
        update_method=async_update_data,
        update_interval=timedelta(seconds=10),
    )



    async def refresh_data_now():
        """Fetch data from API endpoint."""
        _LOGGER.debug("Fetching data from API")
        await coordinator.async_request_refresh()

    coordinator.refresh_data = refresh_data_now









    # Store the coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward the setup to the defined platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("MyPlugin integration successfully set up for %s", base_url)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("MyPlugin integration unloaded successfully.")
    else:
        _LOGGER.error("Failed to unload MyPlugin integration.")

    return unload_ok