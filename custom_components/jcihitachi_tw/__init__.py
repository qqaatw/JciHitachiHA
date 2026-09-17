"""JciHitachi integration."""
import asyncio
import functools
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from queue import Queue
from typing import Optional

import async_timeout
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import discovery
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import (CoordinatorEntity,
                                                      DataUpdateCoordinator,
                                                      UpdateFailed)
from JciHitachi import __version__
from JciHitachi.api import (JciHitachiAuthError, JciHitachiAWSAPI,
                            JciHitachiDeviceError)

from .support_cache import SupportCodeCache
from .const import (API, CONF_DEVICES, CONF_EMAIL, CONF_PASSWORD, CONF_RETRY, SUPPORT_CACHE,
                    CONFIG_SCHEMA, COORDINATOR, DOMAIN, UPDATE_DATA,
                    UPDATED_DATA)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["binary_sensor", "climate", "fan", "humidifier", "select", "sensor", "switch", "light"]
DATA_UPDATE_INTERVAL = timedelta(seconds=30)
BASE_TIMEOUT = 5


def build_coordinator(hass, api, config_entry=None, support_cache=None):

    # Things whose support code was never read cannot get their control entities
    # (climate / humidifier need it). They are asked again, one at a time, after each normal
    # poll; once one answers, a config entry is reloaded so the missing entities get created.
    # A device running on a saved support code (support_cache.py) is still asked every poll.
    pending_things = {
        name
        for name, thing in api.things.items()
        if thing.support_code is None
        or (support_cache is not None and support_cache.uses_saved(name, thing))
    }
    # While a device is pending, every poll also requests the support codes (one extra MQTT
    # phase, up to 10 s). Asking only the pending device in a second refresh_status() call
    # was tried and rejected: the first call marked it available (its status answers),
    # the second marked it unavailable again, so the state and the log flapped every poll.
    timeout = BASE_TIMEOUT + len(api.things) * 2 + (10 if pending_things else 0)

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(timeout):
                await hass.async_add_executor_job(
                    functools.partial(
                        api.refresh_status, refresh_support_code=bool(pending_things)
                    )
                )
                hass.data[DOMAIN][UPDATED_DATA] = api.get_status(legacy=True)

        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Command executed timed out when regularly fetching data.")

        except JciHitachiDeviceError as err:
            # every device failed this round; each thing carries its own attention_reason
            raise UpdateFailed(f"No device answered: {err}")

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

        _LOGGER.debug(
            f"Latest data: {[(name, value.status) for name, value in hass.data[DOMAIN][UPDATED_DATA].items()]}")

        # Must stay last: the reload unloads the entry (and pops hass.data[DOMAIN]) right away,
        # so nothing may touch hass.data[DOMAIN] after scheduling it. Observed 2026-09-17 01:13
        # as "Unexpected error fetching jcihitachi_tw data: KeyError" when this ran earlier.
        recovered = {
            name
            for name in pending_things
            if api.things[name].support_code is not None
            and not (support_cache is not None and support_cache.uses_saved(name, api.things[name]))
        }
        if recovered:
            pending_things.difference_update(recovered)
            rebuild = {
                name
                for name in recovered
                if support_cache is None or support_cache.release(name, api.things[name])
            }
            if support_cache is not None:
                await support_cache.async_save_new(api)
            if rebuild and config_entry is not None:
                _LOGGER.info(
                    f"{', '.join(sorted(rebuild))} answered its support code; reloading the entry to create or update its entities."
                )
                hass.config_entries.async_schedule_reload(config_entry.entry_id)
            elif rebuild:
                _LOGGER.warning(
                    f"{', '.join(sorted(rebuild))} answered its support code; restart Home Assistant to create or update its entities (YAML setup cannot reload)."
                )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name=DOMAIN,
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=DATA_UPDATE_INTERVAL,
    )

    # Reset the update scheduler as the data already exists in
    # `hass.data[DOMAIN][UPDATED_DATA]`.
    coordinator.async_set_updated_data(None)

    return coordinator

async def async_setup(hass, config):
    """Set up from the configuration.yaml"""
    if config.get(DOMAIN, None) is None:
        # skip if no config defined in configuration.yaml"""
        return True
    _LOGGER.debug(
        {
            "CONF_EMAIL": config[DOMAIN].get(CONF_EMAIL),
            "CONF_PASSWORD": '*' * len(config[DOMAIN].get(CONF_PASSWORD)),
            "CONF_RETRY": config[DOMAIN].get(CONF_RETRY),
            "CONF_DEVICES": config[DOMAIN].get(CONF_DEVICES)
        }
    )

    if config[DOMAIN].get(CONF_DEVICES) == []:
        config[DOMAIN][CONF_DEVICES] = None

    api = JciHitachiAWSAPI(
        email=config[DOMAIN].get(CONF_EMAIL),
        password=config[DOMAIN].get(CONF_PASSWORD),
        device_names=config[DOMAIN].get(CONF_DEVICES),
        max_retries=config[DOMAIN].get(CONF_RETRY),
    )

    try:
        await hass.async_add_executor_job(api.login)
    except AssertionError as err:
        _LOGGER.error(f"Assertion check error: {err}")
        return False
    except RuntimeError as err:
        _LOGGER.error(f"Failed to login API: {err}")
        return False

    _LOGGER.debug(f"Backend version: {__version__}")
    _LOGGER.debug(f"Thing info: {[thing for thing in api.things.values()]}")

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][API] = api
    hass.data[DOMAIN][UPDATE_DATA] = Queue()
    hass.data[DOMAIN][SUPPORT_CACHE] = SupportCodeCache(hass)
    await hass.data[DOMAIN][SUPPORT_CACHE].async_load(api)
    hass.data[DOMAIN][UPDATED_DATA] = api.get_status(legacy=True)
    hass.data[DOMAIN][COORDINATOR] = build_coordinator(
        hass, api, support_cache=hass.data[DOMAIN][SUPPORT_CACHE]
    )
    
    # Start jcihitachi components
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
            "CONF_PASSWORD": '*' * len(config.get(CONF_PASSWORD)),
            "CONF_RETRY": config.get(CONF_RETRY),
            "CONF_DEVICES": config.get(CONF_DEVICES)
        }
    )

    if config.get(CONF_DEVICES) == []:
        config[CONF_DEVICES] = None

    if DOMAIN not in hass.data:
        api = JciHitachiAWSAPI(
            email=config.get(CONF_EMAIL),
            password=config.get(CONF_PASSWORD),
            device_names=config.get(CONF_DEVICES),
            max_retries=config.get(CONF_RETRY),
        )

        try:
            await hass.async_add_executor_job(api.login)
        except AssertionError as err:
            _LOGGER.error(f"Assertion check error: {err}")
            return False
        except JciHitachiAuthError as err:
            _LOGGER.error(f"Failed to login API: {err}")
            return False
        except RuntimeError as err:
            # cloud / MQTT hiccup: let Home Assistant retry instead of staying dead until reboot
            raise ConfigEntryNotReady(f"Failed to reach the Hitachi cloud: {err}") from err

        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][API] = api
    else:
        assert API in hass.data[DOMAIN], f"The storage for {DOMAIN} exists but the API instance does not."
        _LOGGER.debug("The API instance has been created in config flow, skipping login.")

    _LOGGER.debug(f"Backend version: {__version__}")
    _LOGGER.debug(f"Thing info: {[thing for thing in hass.data[DOMAIN][API].things.values()]}")
    for thing in hass.data[DOMAIN][API].things.values():
        if not thing.available:
            _LOGGER.warning(
                f"{thing.name} is loaded as unavailable: {thing.attention_reason}"
            )

    hass.data[DOMAIN][UPDATE_DATA] = Queue()
    hass.data[DOMAIN][SUPPORT_CACHE] = SupportCodeCache(hass)
    await hass.data[DOMAIN][SUPPORT_CACHE].async_load(hass.data[DOMAIN][API])
    hass.data[DOMAIN][UPDATED_DATA] = hass.data[DOMAIN][API].get_status(legacy=True)
    hass.data[DOMAIN][COORDINATOR] = build_coordinator(
        hass, hass.data[DOMAIN][API], config_entry, hass.data[DOMAIN][SUPPORT_CACHE]
    )

    # Start jcihitachi components
    _LOGGER.debug("Starting JciHitachi components.") 
    _remove_replaced_month_selectors(hass, hass.data[DOMAIN][API])
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
        
    
    # Return boolean to indicate that initialization was successful.
    return True


def _remove_replaced_month_selectors(hass, api):
    """Remove the 0-12 month selector numbers that the Month Selector drop-down replaced.

    Home Assistant keeps registry entries of entities an integration no longer provides, so every
    device page would show an empty "Month Selector" next to the new drop-down of the same name
    (seen on 2026-09-17). Only this integration's `number` entries with the old unique_id are
    removed; nothing else is touched. Automations using the old entity stop working either way.
    """
    registry = er.async_get(hass)
    for thing in api.things.values():
        unique_id = f"{thing.gateway_mac_address}_monthly_data_selector_number"
        entity_id = registry.async_get_entity_id("number", DOMAIN, unique_id)
        if entity_id is not None:
            registry.async_remove(entity_id)
            _LOGGER.info(
                f"Removed {entity_id}: the month selector is now a drop-down (select entity)."
            )


async def async_unload_entry(hass, config_entry):
    """Unload a config entry (needed for reload after a device recovers)."""
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    if unload_ok:
        data = hass.data.pop(DOMAIN, None)
        if data and API in data:
            await hass.async_add_executor_job(data[API].logout)
    return unload_ok


@dataclass
class UpdateData:
    status_name : str
    device_name : str
    status_value : Optional[int] = field(default_factory=None)
    status_str_value : Optional[str] = field(default_factory=None)


class JciHitachiEntity(CoordinatorEntity):
    # entity names are translation keys (translations/*.json) prefixed with the device name
    _attr_has_entity_name = True

    def __init__(self, thing, coordinator):
        super().__init__(coordinator)
        self._thing = thing

    @property
    def available(self) -> bool:
        return self._thing.available

    @property
    def device_info(self) -> dict:
        """Return device info of the entity."""
        return {
            "identifiers": {(DOMAIN, self._thing.gateway_mac_address)},
            "name": self._thing.name,
            "manufacturer": self._thing.brand,
            "model": self._thing.model,
            "sw_version": self._thing.firmware_version,
        }

    @property
    def unique_id(self):
        """Return the thing's unique id."""
        raise NotImplementedError
    
    def put_queue(self, status_name, status_value=None, status_str_value=None):
        """Put data into the queue to update status"""
        self.hass.data[DOMAIN][UPDATE_DATA].put(
            UpdateData(
                status_name=status_name,
                device_name=self._thing.name,
                status_value=status_value,
                status_str_value=status_str_value
            )
        )
    
    def update(self):
        """Update latest status."""
        api = self.hass.data[DOMAIN][API]

        while self.hass.data[DOMAIN][UPDATE_DATA].qsize() > 0:
            data = self.hass.data[DOMAIN][UPDATE_DATA].get()
            _LOGGER.debug(f"Updating data: {data}")
            result = api.set_status(**vars(data))
            if result is True:
                _LOGGER.debug(f"Data: {data} updated successfully.")
            else:
                _LOGGER.error("Failed to update data.")

        # Here we don't need to refresh status as it was refreshed by `api.set_status`.
        self.hass.data[DOMAIN][UPDATED_DATA] = api.get_status(legacy=True)
        
        _LOGGER.debug(
            f"Latest data: {[(name, value.status) for name, value in self.hass.data[DOMAIN][UPDATED_DATA].items()]}"
        )
        
        # Important: We have to reset the update scheduler to prevent old status from wrongly being loaded. 
        self.hass.loop.call_soon_threadsafe(self.coordinator.async_set_updated_data, None)
