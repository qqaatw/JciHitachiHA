"""JciHitachi integration."""
import logging

from homeassistant import config_entries
from homeassistant.const import CONF_DEVICES, CONF_EMAIL, CONF_PASSWORD
from JciHitachi.api import (JciHitachiAuthError, JciHitachiAWSAPI,
                            JciHitachiDeviceError)

from .const import (API, CONF_ADD_ANOTHER_DEVICE, CONF_RETRY,
                    CONFIG_FLOW_ADD_DEVICE_SCHEMA, CONFIG_FLOW_SCHEMA, DOMAIN)

_LOGGER = logging.getLogger(__name__)

async def validate_auth(hass, email, password, device_names, max_retries) -> None:
    """Validates JciHitachiAWS account and devices."""

    device_names_ = None if device_names == [] else device_names

    api = JciHitachiAWSAPI(
        email=email,
        password=password,
        device_names=device_names_,
        max_retries=max_retries,
    )
    await hass.async_add_executor_job(api.login)

    # login() returns even when every device failed (each thing carries its reason); for the
    # config flow that is still a failure the user must see, so surface it as a device error
    if api.things and not any(thing.available for thing in api.things.values()):
        api.logout()
        raise JciHitachiDeviceError(
            " | ".join(
                f"{name}: {thing.attention_reason}" for name, thing in api.things.items()
            )
        )

    hass.data[DOMAIN] = {API: api}


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
            except JciHitachiAuthError as err:
                _LOGGER.error(f"Failed to login API: {err}")
                errors['base'] = 'login_error'
            except JciHitachiDeviceError as err:
                # account is fine, the devices are not (offline, or answering with a payload
                # the backend cannot decode); details are logged per device by the backend
                _LOGGER.error(f"Logged in, but no device answered: {err}")
                errors['base'] = 'device_error'
            except RuntimeError as err:
                _LOGGER.error(f"Failed to reach the Hitachi cloud: {err}")
                errors['base'] = 'connection_error'
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