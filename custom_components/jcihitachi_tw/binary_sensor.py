"""JciHitachi integration."""
import logging

from homeassistant.components.binary_sensor import (BinarySensorDeviceClass,
                                                    BinarySensorEntity)
from homeassistant.components.logbook import async_log_entry
from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.translation import async_get_translations

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity
from .const import SUPPORT_CACHE

_LOGGER = logging.getLogger(__name__)


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        # every device type can fail to answer; the sensor explains why it is unavailable
        async_add([JciHitachiAttentionBinarySensorEntity(thing, coordinator)],
                  update_before_add=True)
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


class JciHitachiAttentionBinarySensorEntity(JciHitachiEntity, BinarySensorEntity):
    """On when the backend could not refresh this device (timeout or undecodable answer).

    Stays available while the device itself is unavailable: it is the entity that explains why.
    """

    _attr_translation_key = "attention_required"

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    # sentinel: nothing written to the activity log yet for this entity instance
    _NOT_LOGGED = object()

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)
        self._logged_attention = self._NOT_LOGGED

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self):
        return self._thing.attention_reason is not None

    @property
    def extra_state_attributes(self):
        attention = getattr(self._thing, "attention", None) or {}
        return {
            "reason": self._thing.attention_reason,
            "request": attention.get("request"),
            "topic": attention.get("topic"),
            "cause": attention.get("cause"),
            "payload_length": attention.get("payload_length"),
            "payload_hex": attention.get("payload_hex"),
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        await self._async_log_attention()

    @callback
    def _handle_coordinator_update(self) -> None:
        super()._handle_coordinator_update()
        self.hass.async_create_task(self._async_log_attention())

    async def _async_log_attention(self):
        """Write one activity (logbook) entry each time the reason changes, recovery included.

        The attribute `reason` is not shown in the activity log, which only lists on/off changes.
        The text comes from the `exceptions` block of the translations in the server language
        (`hass.config.language`), falling back to English.
        """
        attention = getattr(self._thing, "attention", None)
        previous = self._logged_attention
        if attention == previous:
            return
        self._logged_attention = attention
        if attention is None and previous is self._NOT_LOGGED:
            return  # nothing to report at start-up
        message = await self._async_attention_message(attention)
        async_log_entry(self.hass, self._thing.name, message, DOMAIN, self.entity_id)

    async def _async_attention_message(self, attention):
        language = self.hass.config.language
        strings = await async_get_translations(self.hass, language, "exceptions", {DOMAIN})
        fallback = None

        async def text(key, **placeholders):
            nonlocal fallback
            full_key = f"component.{DOMAIN}.exceptions.{key}.message"
            template = strings.get(full_key)
            if template is None:
                if fallback is None:
                    fallback = await async_get_translations(
                        self.hass, "en", "exceptions", {DOMAIN}
                    )
                template = fallback.get(full_key)
            if template is None:
                return None
            return template.format(**placeholders)

        if attention is None:
            return await text("attention_cleared")
        request_key = attention["request"].replace(" ", "_")
        cache = self.hass.data.get(DOMAIN, {}).get(SUPPORT_CACHE)
        saved_at = cache.saved_at(self._thing.name, self._thing) if cache else None
        parts = [
            await text(
                f"attention_{attention['cause']}",
                request=attention["request"],
                topic=attention["topic"],
                payload_length=attention.get("payload_length"),
                payload_hex=attention.get("payload_hex"),
            ),
            await text("note_support_code_saved", saved_at=saved_at)
            if request_key == "support_code" and saved_at
            else await text(f"note_{request_key}"),
            await text(f"observed_{request_key}_{attention['cause']}"),
        ]
        return " ".join(part for part in parts if part)

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_attention_binary_sensor"


class JciHitachiFreezeCleanNotificationBinarySensorEntity(JciHitachiEntity, BinarySensorEntity):
    """Freeze-clean prompt of an air conditioner, from the numeric status field `CleanNotification`.

    Evidence (2026-09-16, three RAD-series ACs, LibJciHitachi fixtures/observed_2026_09_16):
    the official app showed the freeze-clean prompt for exactly the two units whose
    status/response carried `CleanNotification: 1`; the third unit had 0 and no prompt.
    On 2026-09-17 the field went from 1 to 0 part-way through a freeze clean started from
    this integration, on both units (LibJciHitachi contract profile ac-rad-fw6.0.032).

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