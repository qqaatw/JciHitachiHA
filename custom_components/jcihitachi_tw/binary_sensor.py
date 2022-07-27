"""JciHitachi integration."""
import logging

from homeassistant.components.binary_sensor import (DEVICE_CLASS_PROBLEM,
                                                    BinarySensorEntity)

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        if thing.type == "DH":
            async_add(
                [JciHitachiErrorBinarySensorEntity(thing, coordinator),
                 JciHitachiWaterFullBinarySensorEntity(thing, coordinator)],
                update_before_add=True)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the binary_sensor platform."""
    _async_setup(hass, async_add_entities)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the binary_sensor platform from a config entry."""
    _async_setup(hass, async_add_devices)


class JciHitachiErrorBinarySensorEntity(JciHitachiEntity, BinarySensorEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Error"

    @property
    def is_on(self):
        """Indicate whether an error occurred."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.error_code == 0:
                return False
            else:
                return True
        return None

    @property
    def device_class(self):
        return DEVICE_CLASS_PROBLEM

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_error_binary_sensor"


class JciHitachiWaterFullBinarySensorEntity(JciHitachiEntity, BinarySensorEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Water Full Warning"

    @property
    def is_on(self):
        """Indicate whether the water tank is full."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.water_full_warning == "off":
                return False
            elif status.water_full_warning == "on":
                return True
        return None

    @property
    def device_class(self):
        return DEVICE_CLASS_PROBLEM
    
    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_water_full_binary_sensor"