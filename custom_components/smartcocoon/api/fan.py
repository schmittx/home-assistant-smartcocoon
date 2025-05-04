"""Smart Cocoon API"""
from __future__ import annotations

import logging

from .const import (
    DEFAULT_FAN_NAME,
    FAN_MODE_AUTO,
    FAN_MODE_ECO,
    FAN_MODE_OFF,
    FAN_MODE_ON,
    FAN_MODES,
    METHOD_PUT,
    MODEL_MAP,
    MODEL_UNKNOWN,
    SPEED_LEVEL_MAP,
    SPEED_LEVEL_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


class Fan(object):

    def __init__(self, api, system, room, data):
        self.api = api
        self.system = system
        self.room = room
        self.data = data

    @property
    def id(self) -> int | None:
        return self.data.get("id")

    @property
    def fan_id(self) -> str | None:
        return self.data.get("fan_id")

    @property
    def fan_id_location(self) -> str:
        return f"{self.fan_id} ({self.room.name})"

    @property
    def mqtt_password(self) -> str | None:
        return self.data.get("mqtt_password")

    @property
    def last_connection(self) -> str | None:
        return self.data.get("last_connection")

    @property
    def fan_on(self) -> bool | None:
        return self.data.get("fan_on")

    @property
    def power(self) -> int | None:
        return self.data.get("power")

    @property
    def power_pct(self) -> int | None:
        if self.power:
            return int(self.power / 100)
        return None

    @power_pct.setter
    def power_pct(self, value: int) -> None:
        _LOGGER.debug(f"Setting power level for: {self.id} with raw value: {value}")
        value = int(value * 100)
        _LOGGER.debug(f"Setting power level for: {self.id} with converted value: {value}")
        self.api.call(
            method=METHOD_PUT,
            url=f"fans/{self.id}",
            json={"power": value},
        )

    def set_power_pct(self, value) -> None:
        setattr(self, "power_pct", value)

    @property
    def speed_level(self) -> int | None:
        return self.data.get("speed_level")

    @property
    def speed_level_pct(self) -> str:
        if self.speed_level:
            return SPEED_LEVEL_MAP.get(self.speed_level, SPEED_LEVEL_UNKNOWN)
        return SPEED_LEVEL_UNKNOWN

    @speed_level_pct.setter
    def speed_level_pct(self, value: str) -> None:
        _LOGGER.debug(f"Setting speed level for: {self.id} with raw value: {value}")
        if value not in self.speed_level_pct_options:
            _LOGGER.debug(f"Unable to set speed level for: {self.id} with raw value: {value}")
            return
        value = list(SPEED_LEVEL_MAP.keys())[self.speed_level_pct_options.index(value)]
        _LOGGER.debug(f"Setting speed level for: {self.id} with converted value: {value}")
        self.api.call(
            method=METHOD_PUT,
            url=f"fans/{self.id}",
            json={"speed_level": value},
        )

    @property
    def speed_level_pct_options(self) -> list[str]:
        return list(SPEED_LEVEL_MAP.values())

    @property
    def firmware_version(self) -> str | None:
        return self.data.get("firmware_version")

    @property
    def mode(self) -> str | None:
        return self.data.get("mode")

    @mode.setter
    def mode(self, value: str) -> None:
        if value not in FAN_MODES:
            _LOGGER.debug(f"Unable to set mode for: {self.id} with value: {value}")
            return
        _LOGGER.debug(f"Setting mode for: {self.id} with value: {value}")
        self.api.call(
            method=METHOD_PUT,
            url=f"fans/{self.id}",
            json={"mode": value},
        )

    @property
    def mode_options(self) -> list[str]:
        return FAN_MODES

    def turn_off(self) -> None:
        setattr(self, "mode", FAN_MODE_OFF)

    def turn_on(self, mode: str = FAN_MODE_ON, power_pct: int = None) -> None:
        data = {"mode": mode}
        if power_pct:
            data["power"] = int(power_pct * 100)
        self.api.call(
            method=METHOD_PUT,
            url=f"fans/{self.id}",
            json=data,
        )

    def set_auto(self) -> None:
        setattr(self, "mode", FAN_MODE_AUTO)

    def set_eco(self) -> None:
        setattr(self, "mode", FAN_MODE_ECO)

    @property
    def size(self) -> int | None:
        return self.data.get("size")

    @property
    def model_name(self) -> str:
        return MODEL_MAP.get(self.size, MODEL_UNKNOWN)

    @property
    def mqtt_username(self) -> str | None:
        return self.data.get("mqtt_username")

    @property
    def name(self) -> str:
        if name := self.data.get("name"):
            return name
        return f"{DEFAULT_FAN_NAME} ({self.fan_id})"

    @property
    def name_location(self) -> str:
        return f"{self.name} ({self.room.name})"

    @property
    def room_id(self) -> int | None:
        return self.data.get("room_id")

    @property
    def predicted_room_temperature(self) -> str | None:
        return self.data.get("predicted_room_temperature")

    @property
    def is_room_estimating(self) -> bool | None:
        return self.data.get("is_room_estimating")

    @property
    def is_room_schedule_running(self) -> bool | None:
        return self.data.get("is_room_schedule_running")

    @property
    def thermostat_vendor(self) -> str | None:
        return self.data.get("thermostat_vendor")

    @property
    def connected(self) -> bool | None:
        return self.data.get("connected")
