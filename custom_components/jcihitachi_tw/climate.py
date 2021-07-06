"""JciHitachi integration."""
import logging
import async_timeout
from datetime import timedelta

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from . import API, UPDATE_DATA, JciHitachiEntity, UpdateData


_LOGGER = logging.getLogger(__name__)

SUPPORT_FAN = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
SUPPORT_HVAC = [
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
]
SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the JciHitachi platform."""

    api = hass.data[API]

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                while hass.data[UPDATE_DATA].qsize() > 0:
                    update_data = hass.data[UPDATE_DATA].get()
                    _LOGGER.debug(f"Updating data: {update_data}")
                    result = await hass.async_add_executor_job(api.set_status, update_data.command, update_data.value, update_data.device_name)
                    _LOGGER.debug("Data updated successfully.")

                await hass.async_add_executor_job(api.refresh_status)
                _LOGGER.debug(
                    f"Peripheral Info: {[peripheral for peripheral in api._peripherals.values()]}")
                return api.get_status()
        except Exception as err:
            _LOGGER.error(f"Error communicating with API: {err}")
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="climate",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_refresh()

    for peripheral in api.peripherals.values():
        if peripheral.type == "AC":
            async_add_entities(
                [JciHitachiClimateEntity(
                  peripheral,
                  coordinator)
                ]
            )


class JciHitachiClimateEntity(ClimateEntity, JciHitachiEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(
            peripheral=peripheral,
            coordinator=coordinator
        )

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        status = self.coordinator.data[self._peripheral.name]
        if status:
            return status.indoor_temp
        return None

    @property
    def target_temperature(self):
        """Return the target temperature."""
        status = self.coordinator.data[self._peripheral.name]
        if status:
            return status.target_temp
        return None

    @property
    def target_temperature_step(self):
        """Return the target temperature step."""
        return 1.0

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 32
    
    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 16

    @property
    def hvac_mode(self):
        status = self.coordinator.data[self._peripheral.name]
        if status:
            if status.power == "off":
                return HVAC_MODE_OFF
            elif status.mode == "cool":
                return HVAC_MODE_COOL
            elif status.mode == "dry":
                return HVAC_MODE_DRY
            elif status.mode == "fan":
                return HVAC_MODE_FAN_ONLY
            elif status.mode == "auto":
                return HVAC_MODE_AUTO
            elif status.mode == "heat":
                return HVAC_MODE_HEAT

        _LOGGER.error("Missing hvac_mode")
        return None

    @property
    def hvac_modes(self):
        return SUPPORT_HVAC

    @property
    def fan_mode(self):
        status = self.coordinator.data[self._peripheral.name]
        if status:
            if status.air_speed == "auto":
                return FAN_AUTO
            elif status.air_speed == "silent":
                return FAN_LOW
            elif status.air_speed == "low":
                return FAN_LOW
            elif status.air_speed == "moderate":
                return FAN_MEDIUM
            elif status.air_speed == "high":
                return FAN_HIGH
        _LOGGER.error("Missing fan_mode.")
        return None
    
    @property
    def fan_modes(self):
        return SUPPORT_FAN

    async def update(self, command, value, device_name):
        self.coordinator.hass.data[UPDATE_DATA].put(
            UpdateData(
                command,
                value,
                device_name)
        )
        await self.coordinator.async_request_refresh()

        return True

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

        _LOGGER.debug(f"Set {self.name} hvac_mode to {hvac_mode}")

        status = self.coordinator.data[self._peripheral.name]
        if status.power == "off" and hvac_mode != HVAC_MODE_OFF:
            ret = await self.update("power", 1, self._peripheral.name)
            if not ret:
                _LOGGER.error("Powering on device failed.")
                return

        if hvac_mode == HVAC_MODE_OFF:
            ret = await self.update("power", 0, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_COOL:
            ret = await self.update("mode", 0, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_DRY:
            ret = await self.update("mode", 1, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_FAN_ONLY:
            ret = await self.update("mode", 2, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_AUTO:
            ret = await self.update("mode", 3, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_HEAT:
            ret = await self.update("mode", 4, self._peripheral.name)
        else:
            ret = False
            _LOGGER.error("Invalid hvac_mode.")

        if not ret:
            _LOGGER.error("Setting hvac_mode failed.")

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""

        _LOGGER.debug(f"Set {self.name} fan_mode to {fan_mode}")

        if fan_mode == FAN_AUTO:
            ret = await self.update("air_speed", 0, self._peripheral.name)
        elif fan_mode == FAN_LOW:
            ret = await self.update("air_speed", 1, self._peripheral.name)
        elif fan_mode == FAN_MEDIUM:
            ret = await self.update("air_speed", 3, self._peripheral.name)
        elif fan_mode == FAN_HIGH:
            ret = await self.update("air_speed", 4, self._peripheral.name)
        else:
            ret = False
            _LOGGER.error("Invalid fan_mode.")

        if not ret:
            _LOGGER.error("Setting fan_mode failed.")

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            _LOGGER.error("Missing target temperature %s", kwargs)
            return

        target_temp = int(target_temp)
        _LOGGER.debug("Set %s temperature %s", self.name, target_temp)
        # Limit the target temperature into acceptable range.
        target_temp = min(self.max_temp, target_temp)
        target_temp = max(self.min_temp, target_temp)
        ret = await self.update("target_temp", target_temp, self._peripheral.name)

        if not ret:
            _LOGGER.error("Setting temperature failed.")
