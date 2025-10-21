"""Resolume Arena integration."""
from homeassistant.const import CONF_HOST, CONF_PORT
from .coordinator import ResolumeDataUpdateCoordinator
from .const import DOMAIN

PLATFORMS = ["button", "sensor", "binary_sensor"]

async def async_setup_entry(hass, entry):
    """Set up the integration from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    coordinator = ResolumeDataUpdateCoordinator(hass, host, port)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass, entry):
    """Unload the integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
