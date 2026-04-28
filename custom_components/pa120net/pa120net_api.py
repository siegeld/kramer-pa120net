# pa120net_api.py
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class PA120NetAPI:
    def __init__(self, host, port, loop):
        self._host = host
        self._port = port
        self._loop = loop
        self._reader = None
        self._writer = None
        self.volume = 0          # Initial volume
        self.is_muted = False    # Initial mute state (False = not muted)
        self.connected = False
        self._callbacks = []

    async def connect(self):
        while not self.connected:
            try:
                _LOGGER.debug("Attempting to connect to %s:%s", self._host, self._port)
                self._reader, self._writer = await asyncio.open_connection(
                    self._host, self._port
                )
                self.connected = True
                _LOGGER.info("Connected to PA120Net at %s:%s", self._host, self._port)
                self._loop.create_task(self._listen())
                # The amp's auto-standby puts the audio subsystem to sleep,
                # which makes every AUD-* command return ERR 033 until it's
                # woken. #AUD-STANDBY 3,<5|10|15> rearms auto-standby and
                # also wakes the unit, so do that before any audio query.
                await self.wake()
                await self.get_volume()
                await self.get_mute()
            except (ConnectionRefusedError, OSError) as e:
                _LOGGER.error("Connection failed: %s", e)
                await asyncio.sleep(5)

    async def _listen(self):
        try:
            while True:
                data = await self._reader.readline()
                if not data:
                    _LOGGER.warning("Connection closed by the device.")
                    self.connected = False
                    break
                message = data.decode().strip()
                _LOGGER.debug("Received message: %s", message)
                if message.startswith("~"):
                    await self._handle_response(message)
        except (asyncio.IncompleteReadError, ConnectionResetError) as e:
            _LOGGER.error("Connection lost: %s", e)
            self.connected = False
        finally:
            await self.connect()

    async def _handle_response(self, message):
        if message.startswith("~01@AUD-LVL"):
            # Volume response
            try:
                parts = message.split(",")
                volume = int(parts[-1])
                self.volume = volume
                self._notify_state_changed()
                _LOGGER.debug("Updated volume to %s", self.volume)
            except (ValueError, IndexError) as e:
                _LOGGER.error("Error parsing volume response: %s", e)
        elif message.startswith("~01@AUD-MUTE"):
            # Mute response
            try:
                parts = message.split(",")
                state = parts[-1]
                self.is_muted = (state == '1')  # '1' means mute enabled
                self._notify_state_changed()
                _LOGGER.debug("Updated mute state to %s", self.is_muted)
            except IndexError as e:
                _LOGGER.error("Error parsing mute response: %s", e)

    async def send_command(self, command):
        if self.connected:
            try:
                self._writer.write(f"{command}\r\n".encode())
                await self._writer.drain()
                _LOGGER.debug("Sent command: %s", command)
            except Exception as e:
                _LOGGER.error("Failed to send command: %s", e)
                self.connected = False
                await self.connect()
        else:
            _LOGGER.warning("Not connected. Cannot send command.")

    async def set_volume(self, volume):
        command = f"#AUD-LVL 1,1,{volume}"
        await self.send_command(command)

    async def set_mute(self, mute):
        # Always wake before muting/unmuting — if the amp is in auto-standby,
        # AUD-MUTE returns ERR 033. wake() is idempotent when already awake
        # (just resets the auto-standby timer).
        await self.wake()
        state = '1' if mute else '0'
        command = f"#AUD-MUTE 1,1,{state}"
        await self.send_command(command)

    async def wake(self):
        """Wake the audio subsystem from auto-standby.

        The PA-120Net only accepts #AUD-STANDBY 3,<5|10|15> (auto-standby
        timer), but issuing it also wakes the audio path, which is the only
        way to get AUD-* commands working again after the unit auto-slept.
        """
        await self.send_command("#AUD-STANDBY 3,15")

    async def get_volume(self):
        # Send command to request current volume, if supported
        await self.send_command("#AUD-LVL? 1,1")

    async def get_mute(self):
        # Send command to request current mute state, if supported
        await self.send_command("#AUD-MUTE? 1,1")

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def _notify_state_changed(self):
        for callback in self._callbacks:
            callback()
