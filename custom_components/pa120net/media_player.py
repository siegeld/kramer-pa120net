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
    """Representation of the PA120Net as a media player."""

    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    def __init__(self, api, entry):
        self._api = api
        self._entry = entry
        self._attr_name = entry.data["name"]
        self._attr_unique_id = entry.entry_id
        self._volume_level = self._convert_volume(api.volume)
        self._is_muted = api.is_muted
        self._available = api.connected
        self._attr_supported_features = (
            MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
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
        """Return the state of the device.

        Reflects the device's AUD-STANDBY state: standby = STATE_OFF, otherwise
        STATE_ON. If the TCP connection is down, falls back to STATE_OFF.
        """
        if not self._api.connected:
            return STATE_OFF
        return STATE_OFF if self._api.is_standby else STATE_ON

    @property
    def available(self):
        """Return True if the device is available."""
        return self._api.connected

    @property
    def volume_level(self):
        """Return the volume level (0..1)."""
        return self._volume_level

    @property
    def is_volume_muted(self):
        """Return True if volume is muted."""
        return self._is_muted

    async def async_set_volume_level(self, volume):
        """Set volume level, volume range is 0..1."""
        # Convert volume level to device-specific value (-80 to 10)
        device_volume = self._convert_volume_to_device(volume)
        await self._api.set_volume(device_volume)
        _LOGGER.debug("Set volume level to %s (%s)", volume, device_volume)

    async def async_mute_volume(self, mute):
        """Mute or unmute the media player."""
        await self._api.set_mute(mute)
        _LOGGER.debug("%s the device", "Muted" if mute else "Unmuted")

    async def async_turn_on(self):
        """Wake the amp from standby."""
        await self._api.set_standby(False)
        _LOGGER.debug("Turn on -> AUD-STANDBY 0")

    async def async_turn_off(self):
        """Put the amp into standby."""
        await self._api.set_standby(True)
        _LOGGER.debug("Turn off -> AUD-STANDBY 1")

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
        self._is_muted = self._api.is_muted
        self.async_write_ha_state()
