# Panda Breath MQTT Bridge

MQTT bridge for the Biqu Panda Breath chamber heater. Enables Home Assistant integration via MQTT Discovery.

## Home Assistant Add-on (recommended)

1. Go to **Settings > Add-ons > Add-on Store**
2. Top-right menu > **Repositories**
3. Add: `https://github.com/alexandru-g/panda-breath-mqtt`
4. Install **Panda Breath MQTT Bridge**
5. Go to the **Configuration** tab and set `ws_host` to your Panda Breath IP or hostname (e.g. `pandabreath.local`)
6. **MQTT credentials:**
   - **Mosquitto add-on users**: credentials are detected automatically — no extra config needed
   - **External MQTT broker**: fill in `mqtt_host`, `mqtt_username`, and `mqtt_password` in the config
7. Start the add-on

## Standalone

```bash
pip install git+https://github.com/alexandru-g/panda-breath-mqtt.git

PB_WS_HOST=pandabreath.local PB_MQTT_HOST=localhost panda-breath-mqtt
```

### Configuration

Set environment variables (prefix `PB_`) or create a `.env` file:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PB_WS_HOST` | yes | — | Device IP or hostname |
| `PB_MQTT_HOST` | no | `localhost` | MQTT broker address |
| `PB_MQTT_PORT` | no | `1883` | MQTT broker port |
| `PB_MQTT_USERNAME` | no | — | MQTT username |
| `PB_MQTT_PASSWORD` | no | — | MQTT password |
| `PB_DEVICE_ID` | no | `panda_breath` | Unique device ID |
| `PB_DEVICE_NAME` | no | `Panda Breath` | Display name in HA |
| `PB_LOG_LEVEL` | no | `INFO` | Log level |

### Docker

```bash
docker run -d \
  -e PB_WS_HOST=pandabreath.local \
  -e PB_MQTT_HOST=192.168.1.10 \
  ghcr.io/alexandru-g/panda-breath-mqtt:latest
```

## Exposed Entities

All entities auto-appear in Home Assistant under **Settings > Devices > MQTT > Panda Breath**:

- **Climate** — thermostat card with current/target temp and on/off
- **Switches** — Power, Drying
- **Selects** — Work Mode, Filament Drying Mode
- **Numbers** — Filter/Heater hotbed temp, Filament drying temp/timer
- **Sensors** — Enclosure temperature, Drying time remaining, Firmware version
- **Button** — Restart device
