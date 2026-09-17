"""JciHitachi integration."""
import datetime
import logging

from homeassistant.components.sensor import (SensorStateClass,
                                             SensorDeviceClass, SensorEntity)
from homeassistant.const import (CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                                 EntityCategory,
                                 PERCENTAGE, UnitOfEnergy, UnitOfTemperature)

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
                 JciHitachiFreezeCleanStatusSensorEntity(thing, coordinator),
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
    _attr_translation_key = "indoor_humidity"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

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
    _attr_translation_key = "pm25"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

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
    _attr_translation_key = "odor_level"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

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
    _attr_translation_key = "power_consumption"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

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
        return SensorStateClass.TOTAL_INCREASING

class JciHitachiMonthlyPowerConsumptionSensorEntity(JciHitachiEntity, SensorEntity):
    _attr_translation_key = "monthly_power_consumption"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

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
    _attr_translation_key = "month_indicator"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

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
    _attr_translation_key = "indoor_temperature"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

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


# CleanStatus value -> state key (translations: entity.sensor.freeze_clean_status.state)
FREEZE_CLEAN_STATES = {0: "idle", 1: "starting", 2: "cleaning"}


class JciHitachiFreezeCleanStatusSensorEntity(JciHitachiEntity, SensorEntity):
    """Freeze clean status of an air conditioner, from the status field `CleanStatus`.

    EXPERIMENTAL. The cloud does not say what the values mean. The names below come from what was
    observed on one device family (LibJciHitachi contract profile ac-rad-fw6.0.032, 2026-09-17,
    7 starts on two units):

    - 0 idle: while idle, after a start the unit did not carry out, after a clean ended or was
      interrupted.
    - 1 starting: appeared within about 1 s of an accepted start and lasted at most 28 s. This is
      our label for that phase. Its length is close to the 30 s environment detection in the
      owner's manual, but nothing shows the two are the same thing.
    - 2 cleaning: the rest of the clean.

    Any other value is shown as unknown, with the integer kept in `raw_value`, so a device that
    reports something else does not break the entity.

    實驗性。雲端沒有說明數值的意思，以下名稱來自單一機體家族的觀察（LibJciHitachi contract
    profile ac-rad-fw6.0.032，2026-09-17，兩台共 7 次啟動）：

    - 0 待機：閒置、機體沒有執行的啟動之後、洗完或中斷之後。
    - 1 啟動中：接受啟動後約 1 秒內出現，最多維持 28 秒。這是我們替這一段取的名字；長度接近
      說明書的 30 秒環境偵測，但沒有證據兩者是同一件事。
    - 2 洗淨中：其餘的洗淨期間。

    其他數值顯示為未知，原始整數保留在 `raw_value`，其他機型回報別的值時實體不會出錯。
    """

    _attr_translation_key = "freeze_clean_status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:snowflake-melt"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(FREEZE_CLEAN_STATES.values())

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)
        self._warned_values = set()

    def _raw_value(self):
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status is None or status.CleanStatus == "unsupported":
            return None
        return status.CleanStatus

    @property
    def native_value(self):
        raw = self._raw_value()
        if raw is None:
            return None
        state = FREEZE_CLEAN_STATES.get(raw)
        if state is None and raw not in self._warned_values:
            self._warned_values.add(raw)
            _LOGGER.warning(
                f"{self._thing.name} reported CleanStatus {raw!r}, a value not observed so far; "
                "shown as unknown (see the raw_value attribute)."
            )
        return state

    @property
    def extra_state_attributes(self):
        return {"raw_value": self._raw_value()}

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_freeze_clean_status_sensor"
