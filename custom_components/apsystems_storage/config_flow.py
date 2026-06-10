"""APsystems Storage config flow."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .apsystems_api import APsystemsStorageApiClient, APsystemsStorageApiError
from .const import CONF_IP, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class APsystemsStorageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for APsystems Storage."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step for user configuration.

        Args:
            user_input: The user input from the form.

        Returns:
            The flow result.

        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Test connection before creating entry
            host = user_input.get(CONF_HOST) or user_input.get(CONF_IP)
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            session = async_get_clientsession(self.hass)
            api_client = APsystemsStorageApiClient(
                host=host, port=port, session=session)

            try:
                await api_client.async_test_connection()
            except APsystemsStorageApiError as err:
                _LOGGER.error("Connection test failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                # Prevent duplicate entries based on IP address
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                _LOGGER.info(
                    "Successfully created APsystems Storage entry for IP: %s", host
                )
                return self.async_create_entry(
                    title=f"APsystems Storage: {host}",
                    data=user_input,
                )

        # Define the configuration form schema with selectors
        data_schema = vol.Schema(
            {
                vol.Required(CONF_IP, default=""): TextSelector(
                    TextSelectorConfig(type="text")
                ),
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    NumberSelector(
                        NumberSelectorConfig(
                            min=1, max=65535, mode=NumberSelectorMode.BOX
                        )
                    ),
                    vol.Coerce(int),
                    vol.Range(min=1, max=65535)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of an existing config entry.

        Args:
            user_input: The user input from the reconfigure form.

        Returns:
            The flow result.

        """
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST) or user_input.get(CONF_IP)
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            session = async_get_clientsession(self.hass)
            api_client = APsystemsStorageApiClient(
                host=host, port=port, session=session
            )

            try:
                await api_client.async_test_connection()
            except APsystemsStorageApiError as err:
                _LOGGER.error("Reconfiguration connection test failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=user_input,
                )

        reconfigure_entry = self._get_reconfigure_entry()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_IP,
                        default=reconfigure_entry.data.get(CONF_IP, ""),
                    ): TextSelector(TextSelectorConfig(type="text")),
                    vol.Required(
                        CONF_PORT,
                        default=reconfigure_entry.data.get(CONF_PORT, DEFAULT_PORT),
                    ): vol.All(
                        NumberSelector(
                            NumberSelectorConfig(
                                min=1, max=65535, mode=NumberSelectorMode.BOX
                            )
                        ),
                        vol.Coerce(int),
                        vol.Range(min=1, max=65535),
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> APsystemsStorageOptionsFlowHandler:
        """Get the options flow for this handler.

        Args:
            config_entry: The config entry.

        Returns:
            The options flow handler.

        """
        return APsystemsStorageOptionsFlowHandler(config_entry)


class APsystemsStorageOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for APsystems Storage."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow.

        Args:
            config_entry: The config entry.

        """
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the integration options.

        Args:
            user_input: The user input from the form.

        Returns:
            The flow result.

        """
        if user_input is not None:
            _LOGGER.info(
                "Successfully updated APsystems Storage options for IP: %s",
                self.config_entry.data.get(CONF_IP),
            )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_PORT,
                        default=self.config_entry.data.get(
                            CONF_PORT, DEFAULT_PORT),
                    ): vol.All(
                        NumberSelector(
                            NumberSelectorConfig(
                                min=1, max=65535, mode=NumberSelectorMode.BOX
                            )
                        ),
                        vol.Coerce(int),
                        vol.Range(min=1, max=65535)
                    ),
                }
            ),
        )
