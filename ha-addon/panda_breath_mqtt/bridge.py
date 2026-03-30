"""Core bridge logic: glues WebSocket client to MQTT client."""

from __future__ import annotations

import asyncio
import json
import logging
import signal

from .config import Settings
from .const import WORK_MODE_FROM_NAME, DRYING_MODE_FROM_NAME
from .discovery import generate_discovery_configs
from .mqtt_client import MQTTClient
from .state import StateTracker
from .ws_client import PandaBreathWS

logger = logging.getLogger(__name__)


class Bridge:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._ws = PandaBreathWS(settings.ws_url, settings.reconnect_interval)
        self._mqtt = MQTTClient(settings)
        self._state = StateTracker()
        self._shutdown = asyncio.Event()
        self._last_publish: dict | None = None

    async def _publish_discovery(self) -> None:
        fw = self._state.state.fw_version
        configs = generate_discovery_configs(self._settings, fw)
        await self._mqtt.publish_discovery(configs)

    async def _publish_state(self, force: bool = False) -> None:
        payload = self._state.to_mqtt_payload()
        if not force and payload == self._last_publish:
            return
        self._last_publish = payload
        await self._mqtt.publish_state(payload)

    def _handle_command(self, key: str, payload: str) -> tuple[str, dict] | None:
        """Translate an MQTT command to a WS namespace + payload. Returns None if unknown."""
        match key:
            case "work_on":
                return ("settings", {"work_on": payload == "ON"})
            case "work_mode":
                val = WORK_MODE_FROM_NAME.get(payload)
                if val is not None:
                    return ("settings", {"work_mode": val})
            case "filament_drying_mode":
                val = DRYING_MODE_FROM_NAME.get(payload)
                if val is not None:
                    return ("settings", {"filament_drying_mode": val})
            case "set_temp" | "filtertemp" | "hotbedtemp" | "filament_temp" | "filament_timer":
                try:
                    return ("settings", {key: int(float(payload))})
                except ValueError:
                    logger.warning("Invalid number for %s: %s", key, payload)
            case "isrunning":
                return ("settings", {"isrunning": 1 if payload == "ON" else 0})
            case "reset":
                return ("settings", {"reset": 1})
            case "climate_mode":
                if payload == "off":
                    return ("settings", {"work_on": False})
                else:
                    # Turn on + set to Power On mode
                    return ("settings", {"work_on": True, "work_mode": 2})
            case "climate_temp":
                try:
                    return ("settings", {"set_temp": int(float(payload))})
                except ValueError:
                    logger.warning("Invalid climate temp: %s", payload)
        return None

    async def _ws_reader(self) -> None:
        """Read WS messages and publish state to MQTT."""
        was_connected = False
        async for data in self._ws.messages():
            if self._shutdown.is_set():
                break
            if not was_connected:
                was_connected = True
                await self._mqtt.publish_online()
                await self._publish_discovery()

            changed = self._state.update(data)
            if changed:
                await self._publish_state()

    async def _mqtt_reader(self) -> None:
        """Read MQTT commands and forward to WS."""
        s = self._settings
        ha_status_topic = f"{s.discovery_prefix}/status"

        async for topic, payload in self._mqtt.run(s.command_topic_prefix, ha_status_topic):
            if self._shutdown.is_set():
                break

            # HA birth message — re-publish discovery + state
            if topic == ha_status_topic and payload == "online":
                logger.info("Home Assistant came online, re-publishing discovery")
                await self._publish_discovery()
                await self._mqtt.publish_online()
                await self._publish_state(force=True)
                continue

            # Command messages
            prefix = s.command_topic_prefix + "/"
            if topic.startswith(prefix):
                key = topic[len(prefix):]
                result = self._handle_command(key, payload)
                if result:
                    namespace, ws_payload = result
                    await self._ws.send_command(namespace, ws_payload)
                    # Optimistically update state so HA doesn't flicker
                    # (device doesn't echo back all fields)
                    self._state.update({namespace: ws_payload})
                    await self._publish_state(force=True)
                    logger.info("Command %s=%s -> WS %s", key, payload, ws_payload)
                else:
                    logger.warning("Unknown command: %s=%s", key, payload)

    async def _heartbeat(self) -> None:
        """Periodically re-publish full state."""
        while not self._shutdown.is_set():
            await asyncio.sleep(self._settings.update_interval)
            if self._ws.connected:
                await self._publish_state(force=True)

    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._shutdown.set)

        logger.info(
            "Starting Panda Breath MQTT bridge (WS: %s, MQTT: %s:%d)",
            self._settings.ws_url,
            self._settings.mqtt_host,
            self._settings.mqtt_port,
        )

        tasks = [
            asyncio.create_task(self._ws_reader(), name="ws_reader"),
            asyncio.create_task(self._mqtt_reader(), name="mqtt_reader"),
            asyncio.create_task(self._heartbeat(), name="heartbeat"),
        ]

        try:
            # Wait for shutdown or any task to fail
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                if task.exception():
                    logger.error("Task %s failed: %s", task.get_name(), task.exception())
        finally:
            logger.info("Shutting down...")
            self._shutdown.set()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self._mqtt.publish_offline()
            await self._ws.disconnect()
            logger.info("Shutdown complete")
