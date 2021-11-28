"""JciHitachi integration."""
import logging

from homeassistant.components.sensor import SensorEntity, STATE_CLASS_TOTAL_INCREASING
from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_PM25,
    DEVICE_CLASS_TEMPERATURE,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
    TEMP_CELSIUS,
)

from . import API, COORDINATOR, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    
    api = hass.data[API]
    coordinator = hass.data[COORDINATOR]

    for peripheral in api.peripherals.values():
        if peripheral.type == "AC":
            async_add_entities(
                [JciHitachiOutdoorTempSensorEntity(peripheral, coordinator),
                 JciHitachiPowerConsumptionSensorEntity(peripheral, coordinator)],
                update_before_add=True)
        elif peripheral.type == "DH":
            async_add_entities(
                [JciHitachiIndoorHumiditySensorEntity(peripheral, coordinator),
                 JciHitachiPM25SensorEntity(peripheral, coordinator),
                 JciHitachiPowerConsumptionSensorEntity(peripheral, coordinator)],
                update_before_add=True)
    

class JciHitachiIndoorHumiditySensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} Indoor Humidity"

    @property
    def state(self):
        """Return the indoor humidity."""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
        if status:
            return status.indoor_humidity
        return None

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_HUMIDITY

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return PERCENTAGE

    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_indoor_humidity_sensor"


class JciHitachiPM25SensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} PM2.5"

    @property
    def state(self):
        """Return the PM2.5 value."""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
        if status:
            return status.pm25_value
        return None

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_PM25

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return CONCENTRATION_MICROGRAMS_PER_CUBIC_METER

    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_pm25_sensor"


class JciHitachiOutdoorTempSensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)
    
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


class JciHitachiPowerConsumptionSensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} Power Consumption"

    @property
    def state(self):
        """Return the power consumption in KW/H"""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
        if status:
            return status.power_kwh
        return None

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_ENERGY

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return ENERGY_KILO_WATT_HOUR

    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_power_consumption_sensor"

    @property
    def state_class(self):
        return STATE_CLASS_TOTAL_INCREASING
