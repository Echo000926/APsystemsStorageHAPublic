"""APsystems Storage integration initialization."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .apsystems_api import APsystemsStorageApiClient
from .const import CONF_IP, DEFAULT_PORT, DEVICE_INFO_KEYS, DOMAIN, MANUFACTURER, MODEL
from .coordinator import APsystemsStorageCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.TEXT,
]


@dataclass
class APsystemsStorageRuntimeData:
    """Runtime data stored in ConfigEntry.runtime_data."""

    api_client: APsystemsStorageApiClient
    coordinator: APsystemsStorageCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up APsystems Storage from a config entry.

    Steps
    -----
    1. Build API client and coordinator.
    2. Perform first data refresh (raises ConfigEntryNotReady on failure).
    3. Pre-populate the device registry with identity fields returned by the
       *devices* endpoint (serial_number, model, sw_version) so that Home
       Assistant displays them on the device info card rather than as
       separate sensor entities.
    4. Forward setup to all platform modules.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry to set up.

    Returns:
        True if setup was successful.

    """
    host = entry.data.get(CONF_HOST) or entry.data.get(CONF_IP)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    session = async_get_clientsession(hass)
    api_client = APsystemsStorageApiClient(host=host, port=port, session=session)
    coordinator = APsystemsStorageCoordinator(hass, api_client)

    # Store runtime data on the config entry (IQS runtime-data rule)
    entry.runtime_data = APsystemsStorageRuntimeData(
        api_client=api_client,
        coordinator=coordinator,
    )

    # Also keep legacy hass.data reference for platform compat
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # First refresh – raises ConfigEntryNotReady if the device is unreachable,
    # which satisfies the IQS test-before-setup rule.
    await coordinator.async_config_entry_first_refresh()

    # ------------------------------------------------------------------
    # Write device identity info from the *devices* endpoint into the
    # Home Assistant device registry.  This replaces the approach of
    # exposing Device ID / Type / Firmware Version as sensor entities,
    # which would clutter the Diagnostic section and misrepresent their
    # nature as static identity fields rather than live measurements.
    #
    # Fields written (see DEVICE_INFO_KEYS in const.py):
    #   dev_id  → serial_number   (shown as "Serial number" on device card)
    #   type    → model           (shown as "Model" on device card)
    #   dev_ver → sw_version      (shown as "Firmware" on device card)
    # ------------------------------------------------------------------
    device_data: dict[str, Any] = (
        coordinator.data.get("devices", {}).get("data", {})
        if coordinator.data
        else {}
    )

    # Build keyword arguments for async_get_or_create from the live data
    registry_kwargs: dict[str, str] = {}
    for api_key, registry_field in DEVICE_INFO_KEYS.items():
        value = device_data.get(api_key)
        if value is not None:
            registry_kwargs[registry_field] = str(value)

    dev_registry = dr.async_get(hass)
    dev_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=MODEL,
        manufacturer=MANUFACTURER,
        **registry_kwargs,
    )

    _LOGGER.debug(
        "Device registry populated for %s: %s", entry.entry_id, registry_kwargs
    )

    # Forward the setup to the defined platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "APsystems Storage integration successfully set up for %s:%s", host, port
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry to unload.

    Returns:
        True if unload was successful.

    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.info("APsystems Storage integration unloaded successfully.")
    else:
        _LOGGER.error("Failed to unload APsystems Storage integration.")

    return unload_ok
