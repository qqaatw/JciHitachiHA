"""JciHitachi integration."""
import logging

from homeassistant import config_entries, exceptions
from homeassistant.const import CONF_DEVICES, CONF_EMAIL, CONF_PASSWORD

from .const import (
    API,
    CONFIG_SCHEMA,
    CONF_RETRY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class JciHitachiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """JciHitachi config flow."""
    
    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        pass
    
    async def async_step_user(self, user_input):
        errors = {}
        _LOGGER.debug("ERROR!!!")
        if user_input is not None:
            return self.async_create_entry(
                title="Config",
                data={
                    DOMAIN: user_input
                }
            )
        
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidSessionToken(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid session token."""
