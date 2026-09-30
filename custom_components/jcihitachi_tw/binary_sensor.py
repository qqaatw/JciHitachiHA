"""JciHitachi integration."""
import logging

from homeassistant.components.binary_sensor import (BinarySensorDeviceClass,
                                                    BinarySensorEntity)

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        if thing.type == "AC":
            async_add([JciHitachiFreezeCleanNotificationBinarySensorEntity(thing, coordinator)],
                      update_before_add=True)
        elif thing.type == "DH":
            async_add(
                [JciHitachiErrorBinarySensorEntity(thing, coordinator),
                 JciHitachiWaterFullBinarySensorEntity(thing, coordinator)],
                update_before_add=True)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the binary_sensor platform."""
    await _async_setup(hass, async_add_entities)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the binary_sensor platform from a config entry."""
    await _async_setup(hass, async_add_devices)


class JciHitachiErrorBinarySensorEntity(JciHitachiEntity, BinarySensorEntity):
    _attr_translation_key = "error"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

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
        return BinarySensorDeviceClass.PROBLEM

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_error_binary_sensor"


class JciHitachiWaterFullBinarySensorEntity(JciHitachiEntity, BinarySensorEntity):
    _attr_translation_key = "water_full"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

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
        return BinarySensorDeviceClass.PROBLEM
    
    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_water_full_binary_sensor"


class JciHitachiFreezeCleanNotificationBinarySensorEntity(JciHitachiEntity, BinarySensorEntity):
    """Freeze-clean prompt of an air conditioner, from the numeric status field `CleanNotification`.

    Evidence (2026-09-16, three RAD-series ACs):
    the official app showed the freeze-clean prompt for exactly the two units whose
    status/response carried `CleanNotification: 1`; the third unit had 0 and no prompt.
    On 2026-09-17 the field went from 1 to 0 part-way through a freeze clean started from
    this integration, on both units.

    No device class: PROBLEM would render on/off as a fault, while the field only says
    whether the unit asks for a freeze clean. The on/off text comes from the translations.
    """

    _attr_translation_key = "freeze_clean_notification"

    @property
    def is_on(self):
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status is None or status.CleanNotification == "unsupported":
            return None
        return status.CleanNotification != 0

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_freeze_clean_notification_binary_sensor"