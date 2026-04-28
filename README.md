# Kramer PA120Net

A Home Assistant custom integration for the [Kramer PA120Net](https://www.kramerav.com/) network-controllable power amplifier. Exposes the amplifier as a media player entity with volume and mute control over TCP.

## How It Works

The integration connects to the PA120Net via TCP and maintains a persistent connection. Volume and mute state changes are pushed from the device in real time — no polling required. If the connection drops, it automatically reconnects.

## Installation

### HACS (Custom Repository)

1. In HACS, go to **Integrations** > **Custom Repositories**
2. Add this repository URL and select **Integration** as the category
3. Install **Kramer PA120Net**
4. Restart Home Assistant

### Manual

Copy `custom_components/pa120net/` into your Home Assistant `custom_components/` directory and restart.

## Setup

Go to **Settings** > **Devices & Services** > **Add Integration** > **PA120Net**.

| Parameter | Description | Default |
|-----------|-------------|---------|
| **Host** | IP address or hostname of the PA120Net | *(required)* |
| **Port** | TCP control port | `5000` |
| **Name** | Display name for the entity | `PA120Net` |

## Features

- **Power on/off** — implemented via mute (`AUD-MUTE`); the PA-120Net's `AUD-STANDBY` command only configures the auto-standby timer and can't be used to put the amp in/out of standby on demand
- **Volume control** — maps the device's -80 dB to +10 dB range to Home Assistant's 0–100% scale
- **Push updates** — state changes from the device (front panel, other controllers) are reflected instantly
- **Auto-reconnect** — recovers automatically if the TCP connection is lost

## Protocol

The integration uses the Kramer Protocol 3000 ASCII command set over TCP:

| Command | Description |
|---------|-------------|
| `#AUD-LVL 1,1,<vol>` | Set volume (-80 to 10) |
| `#AUD-LVL? 1,1` | Query current volume |
| `#AUD-MUTE 1,1,<0\|1>` | Set mute (0=off=on/playing, 1=on=muted/off); used as power on/off |
| `#AUD-MUTE? 1,1` | Query mute state |

## License

MIT
