"""Smart Cocoon API."""

from __future__ import annotations

from http import HTTPMethod
import logging
from typing import Any

from .const import DEFAULT_MODEL_NAME, DEVICE_SIZE_MAP, FanMode

_LOGGER = logging.getLogger(__name__)


class Fan:
    """Fan."""

    def __init__(self, api, system, room, data) -> None:
        """Initialize."""
        self.api = api
        self.system = system
        self.room = room
        self.data = data

    @property
    def id(self) -> int | None:
        """ID."""
        return self.data.get("id")

    @property
    def fan_id(self) -> str | None:
        """Fan ID."""
        return self.data.get("fan_id")

    @property
    def fan_id_location(self) -> str:
        """Fan ID location."""
        return f"{self.fan_id} ({self.room.name})"

    @property
    def mqtt_password(self) -> str | None:
        """MQTT password."""
        return self.data.get("mqtt_password")

    @property
    def last_connection(self) -> str | None:
        """Last connection."""
        return self.data.get("last_connection")

    @property
    def fan_on(self) -> bool | None:
        """Fan on."""
        return self.data.get("fan_on")

    @property
    def power(self) -> int | None:
        """Power."""
        return self.data.get("power")

    @property
    def speed_level(self) -> int | None:
        """Speed level."""
        return self.data.get("speed_level")

    @property
    def firmware_version(self) -> str | None:
        """Firmware version."""
        return self.data.get("firmware_version")

    @property
    def mode(self) -> str | None:
        """Mode."""
        return self.data.get("mode")

    @property
    def mode_options(self) -> list[str]:
        """Mode options."""
        return [mode.value for mode in FanMode]

    @property
    def size(self) -> int | None:
        """Size."""
        return self.data.get("size")

    @property
    def model_name(self) -> str:
        """Model name."""
        if self.size is not None and (size := DEVICE_SIZE_MAP.get(self.size)):
            return f"{DEFAULT_MODEL_NAME} ({size})"
        return DEFAULT_MODEL_NAME

    @property
    def mqtt_username(self) -> str | None:
        """MQTT username."""
        return self.data.get("mqtt_username")

    @property
    def name(self) -> str:
        """Name."""
        if name := self.data.get("name"):
            return name
        return f"{DEFAULT_MODEL_NAME} ({self.fan_id})"

    @property
    def name_location(self) -> str:
        """Name location."""
        return f"{self.name} ({self.room.name})"

    @property
    def room_id(self) -> int | None:
        """Room ID."""
        return self.data.get("room_id")

    @property
    def predicted_room_temperature(self) -> str | None:
        """Predicted room temperature."""
        return self.data.get("predicted_room_temperature")

    @property
    def is_room_estimating(self) -> bool | None:
        """Is room estimating."""
        return self.data.get("is_room_estimating")

    @property
    def is_room_schedule_running(self) -> bool | None:
        """Is room schedule running."""
        return self.data.get("is_room_schedule_running")

    @property
    def thermostat_vendor(self) -> str | None:
        """Thermostat vendor."""
        return self.data.get("thermostat_vendor")

    @property
    def connected(self) -> bool | None:
        """Connected."""
        return self.data.get("connected")

    async def set_property(self, key: str, value: Any) -> None:
        """Set property."""
        if not isinstance(key, str) or not isinstance(value, (bool, int, str)):
            return
        _LOGGER.debug(
            "Setting property for: %s with key: %s and value: %s", self.id, key, value
        )
        await self.api.call(
            method=HTTPMethod.PUT,
            path=f"fans/{self.id}",
            json={key: value},
        )

    async def set_mode(self, mode: str) -> None:
        """Set mode."""
        if not isinstance(mode, str):
            _LOGGER.warning("Unable to set mode for: %s with value: %s", self.id, mode)
            return
        _LOGGER.debug("Setting mode for: %s with value: %s", self.id, mode)
        await self.set_property(key="mode", value=mode)

    async def turn_off(self) -> None:
        """Turn off."""
        await self.set_mode(mode=FanMode.OFF)

    async def turn_on(self) -> None:
        """Turn on."""
        await self.set_mode(mode=FanMode.ON)
