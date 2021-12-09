"""JciHitachi integration."""
import logging

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICES, CONF_EMAIL, CONF_PASSWORD

from JciHitachi.api import JciHitachiAPI

from .const import (
    CONFIG_FLOW_SCHEMA,
    CONFIG_FLOW_ADD_DEVICE_SCHEMA,
    CONF_RETRY,
    CONF_ADD_ANOTHER_DEVICE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_auth(hass, email, password, device_names, max_retries) -> None:
    """Validates JciHitachi account and devices."""

    api = JciHitachiAPI(
        email=email,
        password=password,
        device_names=device_names,
        max_retries=max_retries,
    )
    await hass.async_add_executor_job(api.login)


class JciHitachiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """JciHitachi config flow."""
    
    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = None
    
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.data = user_input
            if isinstance(user_input[CONF_DEVICES], str):
                if user_input[CONF_DEVICES] == "":
                    self.data[CONF_DEVICES] = []
                else:
                    self.data[CONF_DEVICES] = [user_input[CONF_DEVICES]]
            
            if user_input[CONF_ADD_ANOTHER_DEVICE]:
                return await self.async_step_add_device()
            
            try:
                await validate_auth(
                    self.hass,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                    user_input[CONF_DEVICES],
                    user_input[CONF_RETRY]
                )
            except AssertionError as err:
                _LOGGER.error(f"Assertion check error: {err}")
                errors['base'] = 'assertion_check_error'
            except RuntimeError as err:
                _LOGGER.error(f"Failed to login API: {err}")
                errors['base'] = 'login_error'
            except Exception as err:
                _LOGGER.error(f"Failed to login API: {err}")
                errors['base'] = 'unknown_error'

            if not errors:
                return self.async_create_entry(
                    title="JciHitachi TW",
                    data={
                        DOMAIN: user_input
                    }
                )
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_FLOW_SCHEMA, errors=errors
        )

    async def async_step_add_device(self, user_input=None):
        errors = {}
        if user_input is not None:
            if user_input[CONF_DEVICES] != "":
                self.data[CONF_DEVICES].append(user_input[CONF_DEVICES])
            if user_input[CONF_ADD_ANOTHER_DEVICE]:
                return await self.async_step_add_device()
            else:
                self.data[CONF_ADD_ANOTHER_DEVICE] = False
                return await self.async_step_user(self.data)

        return self.async_show_form(
            step_id="add_device", data_schema=CONFIG_FLOW_ADD_DEVICE_SCHEMA, errors=errors
        )