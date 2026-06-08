"""ApsystemsStorage config flow."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_IP, CONF_PORT, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)


class APsystemsStorageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for APsystemsStorage."""

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step for user configuration."""
        errors = {}

        if user_input is not None:
            # Prevent duplicate entries based on IP address
            await self.async_set_unique_id(user_input[CONF_IP])
            self._abort_if_unique_id_configured()

            _LOGGER.info(
                "Successfully created APsystemsStorage entry for IP: %s",
                user_input[CONF_IP]
            )
            return self.async_create_entry(
                title=f"APsystemsStorage: {user_input[CONF_IP]}",
                data=user_input
            )

        # Define the configuration form schema
        data_schema = vol.Schema({
            vol.Required(CONF_IP, default=""): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return APsystemsStorageOptionsFlowHandler(config_entry)


class APsystemsStorageOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for APsystemsStorage."""

    def __init__(self, config_entry):
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the integration options."""
        if user_input is not None:
            _LOGGER.info(
                "Successfully updated APsystemsStorage options for IP: %s",
                self.config_entry.data.get(CONF_IP)
            )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_PORT,
                    default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)
                ): int,
            }),
        )