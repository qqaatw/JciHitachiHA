"""JciHitachi integration."""
import voluptuous as vol
from homeassistant.const import CONF_DEVICES, CONF_EMAIL, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv


DOMAIN = "jcihitachi_tw"
API = "api"
COORDINATOR = "coordinator"
UPDATE_DATA = "update_data"
UPDATED_DATA = "updated_data"

CONF_RETRY = "retry"
DEFAULT_RETRY = 5
DEFAULT_DEVICES = []

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_EMAIL): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_RETRY, default=DEFAULT_RETRY): cv.positive_int,
                vol.Optional(CONF_DEVICES, default=DEFAULT_DEVICES): vol.All(cv.ensure_list, list),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)
