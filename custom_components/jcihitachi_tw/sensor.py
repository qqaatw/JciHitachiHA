import logging

from homeassistant.const import(
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS
)
from homeassistant.components.sensor import SensorEntity

from . import API, UPDATED_DATA

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    
    api = hass.data[API]

    for peripheral in api.peripherals.values():
        if peripheral.type == "AC":
            async_add_entities(
                [JciHitachiOutdoorTempSensorEnitty(peripheral)],
                update_before_add=True)
    

class JciHitachiOutdoorTempSensorEnitty(SensorEntity):
    def __init__(self, peripheral):
        self._peripheral = peripheral
        self._init = False
    
    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} Outdoor Temperature"

    @property
    def state(self):
        """Return the outdoor temperature."""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
        if status:
            return status.outdoor_temp
        return None

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_TEMPERATURE
    
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS
    
    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_outdoor_temp_sensor"

    def update(self):
        _LOGGER.debug(f"Update {self.name} sensor data.")
        while not self._init:
            if self.hass.data[UPDATED_DATA].get(self._peripheral.name, None):
                self._init = True
