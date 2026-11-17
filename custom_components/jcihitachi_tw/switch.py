"""JciHitachi integration."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError
from JciHitachi.model import STATUS_DICT

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)


# The official AC app defines these as 0/1 fields with range-based capability data.
# shortcut: LibJciHitachi 1.7.2 omits these AC fields; remove after upstream support.
for field in ("Ion", "AirPurifier"):
    STATUS_DICT["AC"].setdefault(
        field, {"controllable": True, "is_numeric": True, "legacy_name": None}
    )


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        if thing.type == "AC":
            entities = []
            for field, power in (("Ion", "off"), ("AirPurifier", "on")):
                supported = getattr(thing.support_code, field, None)
                if type(supported) is int and supported >= 1:
                    entities.append(JciHitachiACIonFeatureSwitch(thing, coordinator, field, power))
            async_add(entities)
            if getattr(thing.support_code, "SleepModeRemainingTime", "unsupported") != "unsupported":
                async_add(
                    [JciHitachiACSleepModeSwitchEntity(thing, coordinator)],
                    update_before_add=True)
        elif thing.type == "DH":
            async_add(
                [JciHitachiAirCleaningFilterEntity(thing, coordinator),
                 JciHitachiCleanFilterNotifySwitchEntity(thing, coordinator),
                 JciHitachiMoldPrevSwitchEntity(thing, coordinator),
                 JciHitachiWindSwingableSwitchEntity(thing, coordinator),
                 JciHitachiIonSwitchEntity(thing, coordinator),
                 JciHitachiKeypadLockSwitchEntity(thing, coordinator)],
                update_before_add=True)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch platform."""
    await _async_setup(hass, async_add_entities)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the switch platform from a config entry."""
    await _async_setup(hass, async_add_devices)


class JciHitachiACIonFeatureSwitch(JciHitachiEntity, SwitchEntity):
    """Send the official AC Ion/AirPurifier fields through the existing command queue."""

    _attr_has_entity_name = True
    # Bypass the legacy base name property to use HA entity translations.
    name = SwitchEntity.name

    def __init__(self, thing, coordinator, field, required_power):
        super().__init__(thing, coordinator)
        self._field, self._required_power = field, required_power
        self._attr_translation_key = f"ac_{field.lower()}"

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_ac_{self._field.lower()}_switch"

    @property
    def is_on(self):
        """Return the reported numeric field, preserving missing or invalid values as unknown."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name)
        value = getattr(status, self._field, None)
        return bool(value) if type(value) is int and value in (0, 1) else None

    def _send(self, value):
        """Send once in the required power state; the official app verifies actual execution."""
        if not self._thing.available or self._thing.status_code.Switch != self._required_power:
            raise HomeAssistantError(f"{self._field} requires an available AC with power {self._required_power}.")
        self.put_queue(status_name=self._field, status_value=value)
        self.update()

    def turn_on(self, **kwargs):
        """Request the official feature's on value without retries or a power-mode change."""
        self._send(1)

    def turn_off(self, **kwargs):
        """Request the official feature's off value without retries or a power-mode change."""
        self._send(0)


class JciHitachiAirCleaningFilterEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Air Cleaning Filter Setting"

    @property
    def is_on(self):
        """Indicate whether air cleaning filter setting is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.air_cleaning_filter == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_air_cleaning_filter_switch"

    def turn_on(self):
        """Turn air cleaning filter setting on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="air_cleaning_filter", status_str_value="enabled")
        self.update()

    def turn_off(self):
        """Turn air cleaning filter setting off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="air_cleaning_filter", status_str_value="disabled")
        self.update()


class JciHitachiCleanFilterNotifySwitchEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Clean Filter Notification"

    @property
    def is_on(self):
        """Indicate whether clean filter notification is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.clean_filter_notify == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_clean_filter_notify_switch"

    def turn_on(self):
        """Turn clean filter notification on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="clean_filter_notify", status_str_value="enabled")
        self.update()

    def turn_off(self):
        """Turn clean filter notification off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="clean_filter_notify", status_str_value="disabled")
        self.update()


class JciHitachiMoldPrevSwitchEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Mold Prevention"

    @property
    def is_on(self):
        """Indicate whether mold prevention is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.mold_prev == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_mold_prev_switch"

    def turn_on(self):
        """Turn mold prevention on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="mold_prev", status_str_value="enabled")
        self.update()

    def turn_off(self):
        """Turn mold prevention off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="mold_prev", status_str_value="disabled")
        self.update()


class JciHitachiWindSwingableSwitchEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Wind Swingable"

    @property
    def is_on(self):
        """Indicate whether wind swingable is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.wind_swingable == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_wind_swingable_switch"

    def turn_on(self):
        """Turn wind swingable on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="wind_swingable", status_str_value="enabled")
        self.update()
    
    def turn_off(self):
        """Turn wind swingable off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="wind_swingable", status_str_value="disabled")
        self.update()

class JciHitachiIonSwitchEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Ion"

    @property
    def is_on(self):
        """Indicate whether ion is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.Ion == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_ion_switch"

    def turn_on(self):
        """Turn ion on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="Ion", status_str_value="enabled")
        self.update()
    
    def turn_off(self):
        """Turn ion off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="Ion", status_str_value="disabled")
        self.update()

class JciHitachiKeypadLockSwitchEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Keypad Lock"

    @property
    def is_on(self):
        """Indicate whether keypad lock is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.KeypadLock == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_keypad_lock_switch"

    def turn_on(self):
        """Turn keypad lock on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="KeypadLock", status_str_value="enabled")
        self.update()
    
    def turn_off(self):
        """Turn keypad lock off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="KeypadLock", status_str_value="disabled")
        self.update()


class JciHitachiACSleepModeSwitchEntity(JciHitachiEntity, SwitchEntity):
    """Comfort sleep (舒眠) countdown switch for air conditioner."""

    DEFAULT_SLEEP_MINUTES = 480  # 8 hours

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)
        self._last_minutes = 0

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Sleep Mode"

    @property
    def is_on(self):
        """Indicate whether sleep mode is counting down."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            value = status.sleep_timer
            if isinstance(value, int) and value > 0:
                self._last_minutes = value
                return True
            elif value == 0:
                return False
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_sleep_mode_switch"

    def turn_on(self):
        """Turn sleep mode on with the last known duration."""
        minutes = self._last_minutes or self.DEFAULT_SLEEP_MINUTES
        support = getattr(self._thing.support_code, "SleepModeRemainingTime", "unsupported")
        if isinstance(support, int) and support > 0:
            minutes = min(minutes, support)
        _LOGGER.debug(f"Turn {self.name} on with {minutes} minutes")
        self.put_queue(status_name="sleep_timer", status_value=minutes)
        self.update()

    def turn_off(self):
        """Cancel sleep mode."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="sleep_timer", status_value=0)
        self.update()
