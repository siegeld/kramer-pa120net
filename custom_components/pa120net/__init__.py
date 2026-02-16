# __init__.py
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .pa120net_api import PA120NetAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["media_player"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the PA120Net component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up PA120Net from a config entry."""
    host = entry.data["host"]
    port = entry.data["port"]

    loop = asyncio.get_event_loop()
    api = PA120NetAPI(host, port, loop)
    hass.data[DOMAIN][entry.entry_id] = api
    await api.connect()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        api = hass.data[DOMAIN].pop(entry.entry_id)
        if api.connected:
            api._writer.close()
            await api._writer.wait_closed()
    return unload_ok
