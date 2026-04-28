# media_player.py
import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerDeviceClass,
    MediaPlayerEntityFeature,
)
from homeassistant.core import callback
from homeassistant.const import STATE_ON, STATE_OFF

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the PA120Net media player."""
    api = hass.data[DOMAIN][entry.entry_id]
    player = PA120NetMediaPlayer(api, entry)
    async_add_entities([player])

class PA120NetMediaPlayer(MediaPlayerEntity):
    """Representation of the PA120Net as a media player.

    The amp's Protocol 3000 AUD-STANDBY command can't actually drive the unit
    in/out of standby (only the auto-standby timeout is settable), so power
    on/off is implemented via AUD-MUTE. Mute is therefore not exposed as a
    separate feature.
    """

    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    def __init__(self, api, entry):
        self._api = api
        self._entry = entry
        self._attr_name = entry.data["name"]
        self._attr_unique_id = entry.entry_id
        self._volume_level = self._convert_volume(api.volume)
        self._available = api.connected
        self._attr_supported_features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
        )
        self._api.register_callback(self._update_state)

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._attr_name,
            "manufacturer": "Kramer",
            "model": "PA120Net Model",
        }

    @property
    def state(self):
        """Power state derived from mute: muted = off, unmuted = on."""
        if not self._api.connected:
            return STATE_OFF
        return STATE_OFF if self._api.is_muted else STATE_ON

    @property
    def available(self):
        """Return True if the device is available."""
        return self._api.connected

    @property
    def volume_level(self):
        """Return the volume level (0..1)."""
        return self._volume_level

    async def async_set_volume_level(self, volume):
        """Set volume level, volume range is 0..1."""
        # Convert volume level to device-specific value (-80 to 10)
        device_volume = self._convert_volume_to_device(volume)
        await self._api.set_volume(device_volume)
        _LOGGER.debug("Set volume level to %s (%s)", volume, device_volume)

    async def async_turn_on(self):
        """Power on by unmuting."""
        await self._api.set_mute(False)
        _LOGGER.debug("Turn on -> AUD-MUTE 0")

    async def async_turn_off(self):
        """Power off by muting."""
        await self._api.set_mute(True)
        _LOGGER.debug("Turn off -> AUD-MUTE 1")

    def _convert_volume(self, device_volume):
        """Convert device volume (-80 to 10) to Home Assistant volume (0..1)."""
        # Normalize the device volume to a 0..1 range
        return (device_volume + 80) / 90  # Since 10 - (-80) = 90

    def _convert_volume_to_device(self, volume):
        """Convert Home Assistant volume (0..1) to device volume (-80 to 10)."""
        return int(volume * 90 - 80)

    @callback
    def _update_state(self):
        """Update the internal state from the API."""
        self._available = self._api.connected
        self._volume_level = self._convert_volume(self._api.volume)
        self.async_write_ha_state()
