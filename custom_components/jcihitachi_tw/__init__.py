"""JciHitachi integration."""
import logging
from queue import Queue

import voluptuous as vol

from homeassistant.const import CONF_DEVICES, CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from JciHitachi.api import JciHitachiAPI

_LOGGER = logging.getLogger(__name__)

DOMAIN = "jcihitachi_tw"
API = "api"
UPDATE_DATA = "update_data"

CONF_RETRY = "retry"
DEFAULT_RETRY = 5
DEFAULT_DEVICES = []
PLATFORMS = ["climate"]


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_EMAIL): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_RETRY, default=DEFAULT_RETRY): cv.positive_int,
                vol.Optional(CONF_DEVICES, default=DEFAULT_DEVICES): vol.All(cv.ensure_list, list),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    if API not in hass.data:
        hass.data[API] = None

    _LOGGER.debug(
        f"CONF_EMAIL: {config[DOMAIN].get(CONF_EMAIL)}, \
          CONF_PASSWORD: {''.join(['*']*len(config[DOMAIN].get(CONF_EMAIL)))}, \
          CONF_RETRY: {config[DOMAIN].get(CONF_RETRY)}, \
          CONF_DEVICES: {config[DOMAIN].get(CONF_DEVICES)}"
    )

    if len(config[DOMAIN].get(CONF_DEVICES)) == 0:
        config[DOMAIN][CONF_DEVICES] = None

    api = JciHitachiAPI(
        email=config[DOMAIN].get(CONF_EMAIL),
        password=config[DOMAIN].get(CONF_PASSWORD),
        device_names=config[DOMAIN].get(CONF_DEVICES),
        max_retries=config[DOMAIN].get(CONF_RETRY),
    )

    try:
        api.login()
    except AssertionError:
        _LOGGER.error("Specified device(s) is/are not available from the API.")
        return False
    except RuntimeError:
        _LOGGER.error("Failed to login API.")
        return False

    hass.data[API] = api
    hass.data[UPDATE_DATA] = Queue()

    # Start jcihitachi components
    if hass.data[API]:
        _LOGGER.debug("Starting jcihitachi components.")
        for platform in PLATFORMS:
            discovery.load_platform(hass, platform, DOMAIN, {}, config)
    # Return boolean to indicate that initialization was successful.
    return True


class UpdateData:
    def __init__(self, command, value, device_name):
        self.command = command
        self.value = value
        self.device_name = device_name
    
    def __repr__(self):
        return str(self.__dict__)
    

class JciHitachiEntity(CoordinatorEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(coordinator)
        self._peripheral = peripheral

    @property
    def should_poll(self):
        """Need polling."""
        return True

    @property
    def name(self):
        """Return the peripheral's name."""
        return self._peripheral.name

    @property
    def unique_id(self):
        """Return the peripheral's unique id."""
        return self._peripheral.gateway_mac_address
    
    async def update(self, command, value, device_name):
        self.coordinator.hass.data[UPDATE_DATA].put(
            UpdateData(
                command,
                value,
                device_name
            )
        )
    
    async def refresh(self):
        await self.coordinator.async_request_refresh()
        return True
