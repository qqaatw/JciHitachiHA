"""JciHitachi integration."""
import datetime
import logging

from homeassistant.components.sensor import (STATE_CLASS_MEASUREMENT,
                                             STATE_CLASS_TOTAL_INCREASING,
                                             SensorDeviceClass,
                                             SensorEntity)
from homeassistant.const import (CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, PERCENTAGE,
                                 UnitOfEnergy, UnitOfTemperature)

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)

ODOR_LEVEL_LOW = "Low"
ODOR_LEVEL_MIDDLE = "Middle"
ODOR_LEVEL_HIGH = "High"
ODOR_LEVELS = [
    ODOR_LEVEL_LOW,
    ODOR_LEVEL_MIDDLE,
    ODOR_LEVEL_HIGH,
]


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        if thing.type == "AC":
            async_add(
                [JciHitachiPowerConsumptionSensorEntity(thing, coordinator),
                 JciHitachiMonthlyPowerConsumptionSensorEntity(thing, coordinator),
                 JciHitachiMonthIndicatorSensorEntity(thing, coordinator),
                 ],
                update_before_add=True)
        elif thing.type == "DH":
            async_add(
                [JciHitachiIndoorHumiditySensorEntity(thing, coordinator),
                 JciHitachiOdorLevelSensorEntity(thing, coordinator),
                 JciHitachiPM25SensorEntity(thing, coordinator),
                 JciHitachiPowerConsumptionSensorEntity(thing, coordinator),
                 JciHitachiMonthlyPowerConsumptionSensorEntity(thing, coordinator),
                 JciHitachiMonthIndicatorSensorEntity(thing, coordinator),
                 ],
                update_before_add=True)
        elif thing.type == "HE":
            async_add(
                [JciHitachiIndoorTemperatureSensorEntity(thing, coordinator),
                 ], 
                 update_before_add=True
            )

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    await _async_setup(hass, async_add_entities)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the sensor platform from a config entry."""
    await _async_setup(hass, async_add_devices)


class JciHitachiIndoorHumiditySensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Indoor Humidity"

    @property
    def native_value(self):
        """Return the indoor humidity."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            return None if status.indoor_humidity == "unsupported" else status.indoor_humidity
        return None

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.HUMIDITY

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return PERCENTAGE

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_indoor_humidity_sensor"


class JciHitachiPM25SensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} PM2.5"

    @property
    def native_value(self):
        """Return the PM2.5 value."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            return None if status.pm25_value == "unsupported" else status.pm25_value
        return None

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.PM25

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return CONCENTRATION_MICROGRAMS_PER_CUBIC_METER

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_pm25_sensor"


class JciHitachiOdorLevelSensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Odor Level"

    @property
    def native_value(self):
        """Return the odor level."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.odor_level == "low":
                return ODOR_LEVEL_LOW
            elif status.odor_level == "middle":
                return ODOR_LEVEL_MIDDLE
            elif status.odor_level == "high":
                return ODOR_LEVEL_HIGH
        return None
    
    @property
    def options(self):
        """Return all odor levels."""
        return ODOR_LEVELS
    
    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.ENUM

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_odor_level_sensor"


class JciHitachiPowerConsumptionSensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Power Consumption"

    @property
    def native_value(self):
        """Return the power consumption in KW/H"""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            return None if status.power_kwh == "unsupported" else status.power_kwh
        return None

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.ENERGY

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_power_consumption_sensor"

    @property
    def state_class(self):
        return STATE_CLASS_TOTAL_INCREASING

class JciHitachiMonthlyPowerConsumptionSensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Monthly Power Consumption"

    @property
    def native_value(self):
        """Return the monthly power consumption in KW/H"""
        monthly_data = self._thing.monthly_data
        if monthly_data:
            return monthly_data[0]["PowerConsumption_Sum"] / 10
        return -1

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.ENERGY

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_monthly_power_consumption_sensor"
    
    @property
    def state_class(self):
        return None

class JciHitachiMonthIndicatorSensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Month Indicator"

    @property
    def state(self):
        """Return the month in yyyy-mm format."""
        value = self.native_value
        if value is not None:
            return self.native_value.strftime("%Y-%m")
        return None
        
    @property
    def native_value(self):
        """Return the month in datetime.date object."""
        monthly_data = self._thing.monthly_data
        if monthly_data:
            return datetime.date.fromtimestamp(monthly_data[0]["Timestamp"] / 1000)
        return None

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.DATE

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_month_indicator_sensor"


class JciHitachiIndoorTemperatureSensorEntity(JciHitachiEntity, SensorEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Indoor Temperature"

    @property
    def native_value(self):
        """Return the indoor temperature."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            return None if status.IndoorTemperature == "unsupported" else status.IndoorTemperature
        return None

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_indoor_temperature_sensor"