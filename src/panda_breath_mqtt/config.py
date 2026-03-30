"""Configuration via environment variables (prefix PB_) or .env file."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    model_config = {"env_prefix": "PB_", "env_file": ".env", "env_file_encoding": "utf-8"}

    # WebSocket
    ws_host: str = Field(description="Panda Breath IP or hostname")
    ws_port: int = 80
    ws_path: str = "/ws"

    # MQTT
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None

    # Topics
    mqtt_base_topic: str = "panda_breath"
    discovery_prefix: str = "homeassistant"

    # Device identity
    device_id: str = "panda_breath"
    device_name: str = "Panda Breath"

    # Behavior
    update_interval: int = 30  # seconds, max between full state publishes
    reconnect_interval: int = 5  # seconds between reconnect attempts
    log_level: str = "INFO"

    @property
    def ws_url(self) -> str:
        return f"ws://{self.ws_host}:{self.ws_port}{self.ws_path}"

    @property
    def base_topic(self) -> str:
        return f"{self.mqtt_base_topic}/{self.device_id}"

    @property
    def availability_topic(self) -> str:
        return f"{self.base_topic}/availability"

    @property
    def state_topic(self) -> str:
        return f"{self.base_topic}/state"

    @property
    def command_topic_prefix(self) -> str:
        return f"{self.base_topic}/cmd"

    @property
    def configuration_url(self) -> str:
        return f"http://{self.ws_host}"
