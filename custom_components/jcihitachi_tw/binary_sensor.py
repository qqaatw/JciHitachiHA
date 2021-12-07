"""JciHitachi integration."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, DEVICE_CLASS_PROBLEM

from . import API, COORDINATOR, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the binary sensor platform."""

    api = hass.data[API]
    coordinator = hass.data[COORDINATOR]

    for peripheral in api.peripherals.values():
        if peripheral.type == "DH":
            async_add_entities(
                [JciHitachiErrorBinarySensorEntity(peripheral, coordinator),
                 JciHitachiWaterFullBinarySensorEntity(peripheral, coordinator)],
                update_before_add=True)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the binary sensor platform from a config entry."""

    api = hass.data[API]
    coordinator = hass.data[COORDINATOR]

    for peripheral in api.peripherals.values():
        if peripheral.type == "DH":
            async_add_devices(
                [JciHitachiErrorBinarySensorEntity(peripheral, coordinator),
                 JciHitachiWaterFullBinarySensorEntity(peripheral, coordinator)],
                update_before_add=True)


class JciHitachiErrorBinarySensorEntity(JciHitachiEntity, BinarySensorEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} Error"

    @property
    def is_on(self):
        """Indicate whether an error occurred."""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
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
        return f"{self._peripheral.gateway_mac_address}_error_binary_sensor"


class JciHitachiWaterFullBinarySensorEntity(JciHitachiEntity, BinarySensorEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} Water Full Warning"

    @property
    def is_on(self):
        """Indicate whether the water tank is full."""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
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
        return f"{self._peripheral.gateway_mac_address}_water_full_binary_sensor"

