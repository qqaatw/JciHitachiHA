"""JciHitachi integration."""
import asyncio
import async_timeout
import logging
from datetime import timedelta
from queue import Queue
from typing import NamedTuple

from homeassistant.helpers import discovery
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed
)

from JciHitachi.api import JciHitachiAPI

from .const import (
    CONF_DEVICES,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_RETRY,
    CONFIG_SCHEMA,
    DOMAIN,
    API,
    COORDINATOR,
    UPDATE_DATA,
    UPDATED_DATA,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "climate", "fan", "humidifier", "sensor", "switch"]
DATA_UPDATE_INTERVAL = timedelta(seconds=30)


async def async_setup(hass, config):
    """Set up from the configuration.yaml"""
    if config.get(DOMAIN, None) is None:
        # skip if no config defined in configuration.yaml"""
        return True
    _LOGGER.debug(
        {
            "CONF_EMAIL": config[DOMAIN].get(CONF_EMAIL),
            "CONF_PASSWORD": ''.join(['*']*len(config[DOMAIN].get(CONF_PASSWORD))),
            "CONF_RETRY": config[DOMAIN].get(CONF_RETRY),
            "CONF_DEVICES": config[DOMAIN].get(CONF_DEVICES)
        }
    )

    if config[DOMAIN].get(CONF_DEVICES) == []:
        config[DOMAIN][CONF_DEVICES] = None

    api = JciHitachiAPI(
        email=config[DOMAIN].get(CONF_EMAIL),
        password=config[DOMAIN].get(CONF_PASSWORD),
        device_names=config[DOMAIN].get(CONF_DEVICES),
        max_retries=config[DOMAIN].get(CONF_RETRY),
    )

    hass.data[API] = api
    hass.data[UPDATE_DATA] = Queue()
    hass.data[UPDATED_DATA] = dict()
    hass.data[COORDINATOR] = None

    try:
        await hass.async_add_executor_job(api.login)
    except AssertionError as err:
        _LOGGER.error(f"Assertion check error: {err}")
        return False
    except RuntimeError as err:
        _LOGGER.error(f"Failed to login API: {err}")
        return False

    _LOGGER.debug(
        f"Peripheral info: {[peripheral for peripheral in api.peripherals.values()]}")
    
    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                await hass.async_add_executor_job(api.refresh_status)
                hass.data[UPDATED_DATA] = api.get_status()

        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Command executed timed out when regularly fetching data.")

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        
        _LOGGER.debug(
            f"Latest data: {[(name, value.status) for name, value in hass.data[UPDATED_DATA].items()]}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name=DOMAIN,
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=DATA_UPDATE_INTERVAL,
    )

    await coordinator.async_refresh()

    hass.data[COORDINATOR] = coordinator
    
    # Start jcihitachi components
    if hass.data[API]:
        _LOGGER.debug("Starting JciHitachi components.")
        for platform in PLATFORMS:
            discovery.load_platform(hass, platform, DOMAIN, {}, config)

    # Return boolean to indicate that initialization was successful.
    return True

async def async_setup_entry(hass, config_entry):
    """Set up from a config entry."""

    config = config_entry.data[DOMAIN]
    _LOGGER.debug(
        {
            "CONF_EMAIL": config.get(CONF_EMAIL),
            "CONF_PASSWORD": ''.join(['*']*len(config.get(CONF_PASSWORD))),
            "CONF_RETRY": config.get(CONF_RETRY),
            "CONF_DEVICES": config.get(CONF_DEVICES)
        }
    )

    if config.get(CONF_DEVICES) == []:
        config[CONF_DEVICES] = None

    api = JciHitachiAPI(
        email=config.get(CONF_EMAIL),
        password=config.get(CONF_PASSWORD),
        device_names=config.get(CONF_DEVICES),
        max_retries=config.get(CONF_RETRY),
    )

    hass.data[API] = api
    hass.data[UPDATE_DATA] = Queue()
    hass.data[UPDATED_DATA] = dict()
    hass.data[COORDINATOR] = None

    try:
        await hass.async_add_executor_job(api.login)
    except AssertionError as err:
        _LOGGER.error(f"Assertion check error: {err}")
        return False
    except RuntimeError as err:
        _LOGGER.error(f"Failed to login API: {err}")
        return False

    _LOGGER.debug(
        f"Peripheral info: {[peripheral for peripheral in api.peripherals.values()]}")
    
    async def _async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                await hass.async_add_executor_job(api.refresh_status)
                hass.data[UPDATED_DATA] = api.get_status()

        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Command executed timed out when regularly fetching data.")

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

        _LOGGER.debug(
            f"Latest data: {[(name, value.status) for name, value in hass.data[UPDATED_DATA].items()]}")

    def _async_forward_entry_setup():
        for platform in PLATFORMS:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(config_entry, platform)
            )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name=DOMAIN,
        update_method=_async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=DATA_UPDATE_INTERVAL,
    )

    await coordinator.async_refresh()

    hass.data[COORDINATOR] = coordinator
    
    # Start jcihitachi components
    if hass.data[API]:
        _LOGGER.debug("Starting JciHitachi components.")
        _async_forward_entry_setup()
    
    # Return boolean to indicate that initialization was successful.
    return True


class JciHitachiEntity(CoordinatorEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(coordinator)
        self._peripheral = peripheral

    @property
    def available(self) -> bool:
        return self._peripheral.available

    @property
    def device_info(self) -> dict:
        """Return device info of the entity."""
        return {
            "identifiers": {(DOMAIN, self._peripheral.gateway_mac_address)},
            "name": self._peripheral.name,
            "manufacturer": self._peripheral.brand,
            "model": self._peripheral.model,
        }

    @property
    def name(self):
        """Return the peripheral's name."""
        return self._peripheral.name

    @property
    def unique_id(self):
        """Return the peripheral's unique id."""
        raise NotImplementedError
    
    def put_queue(self, command, value, device_name):
        """Put data into the queue to update status"""
        self.hass.data[UPDATE_DATA].put(
            UpdateData(command, value, device_name)
        )
    
    def update(self):
        """Update latest status."""
        api = self.hass.data[API]

        while self.hass.data[UPDATE_DATA].qsize() > 0:
            data = self.hass.data[UPDATE_DATA].get()
            _LOGGER.debug(f"Updating data: {data}")
            result = api.set_status(*data)
            if result is True:
                _LOGGER.debug("Data updated successfully.")

        api.refresh_status()
        self.hass.data[UPDATED_DATA] = api.get_status()
        _LOGGER.debug(
            f"Latest data: {[(name, value.status) for name, value in self.hass.data[UPDATED_DATA].items()]}"
        )
        
        # Important: We have to reset the update scheduler to prevent old status from wrongly being loaded. 
        self.coordinator.async_set_updated_data(None)


class UpdateData(NamedTuple):
    command : str
    value : int
    device_name : str
