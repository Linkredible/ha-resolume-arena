"""Config flow for Resolume Arena."""
import logging
import voluptuous as vol
from aiohttp import ClientError

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)

async def validate_input(hass, data):
    """Check that the host/port speak the Resolume HTTP API."""
    session = async_get_clientsession(hass)
    url = f"http://{data[CONF_HOST]}:{data[CONF_PORT]}/api/v1/composition"
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                return { "title": f"Resolume ({data[CONF_HOST]})" }
            _LOGGER.error("Validation failed with status: %s", response.status)
            raise ConnectionError(f"Invalid API response status: {response.status}")
    except ClientError as err:
        _LOGGER.error("Connection error during validation: %s", err)
        raise ConnectionError(f"Connection error: {err}") from err
    except Exception as err:
        _LOGGER.error("Unknown error during validation: %s", err)
        raise ConnectionError(f"Unknown error: {err}") from err

class ResolumeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the configuration flow."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial step for host/port."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
