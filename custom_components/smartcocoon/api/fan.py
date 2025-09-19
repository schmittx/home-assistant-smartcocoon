"""Smart Cocoon API."""

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
    def power_pct(self) -> int | None:
        """Power pct."""
        if self.power:
            return int(self.power / 100)
        return None

    @power_pct.setter
    def power_pct(self, value: int) -> None:
        _LOGGER.debug("Setting power level for: %s with raw value: %s", self.id, value)
        value = int(value * 100)
        _LOGGER.debug(
            "Setting power level for: %s with converted value: %s", self.id, value
        )
        self.api.call(
            method=METHOD_PUT,
            url=f"fans/{self.id}",
            json={"power": value},
        )

    def set_power_pct(self, value) -> None:
        """Set power pct."""
        setattr(self, "power_pct", value)

    @property
    def speed_level(self) -> int | None:
        """Speed level."""
        return self.data.get("speed_level")

    @property
    def speed_level_pct(self) -> str:
        """Speed level pct."""
        if self.speed_level:
            return SPEED_LEVEL_MAP.get(self.speed_level, SPEED_LEVEL_UNKNOWN)
        return SPEED_LEVEL_UNKNOWN

    @speed_level_pct.setter
    def speed_level_pct(self, value: str) -> None:
        _LOGGER.debug("Setting speed level for: %s with raw value: %s", self.id, value)
        if value not in self.speed_level_pct_options:
            _LOGGER.debug(
                "Unable to set speed level for: %s with raw value: %s", self.id, value
            )
            return
        value = list(SPEED_LEVEL_MAP.keys())[self.speed_level_pct_options.index(value)]
        _LOGGER.debug(
            "Setting speed level for: %s with converted value: %s", self.id, value
        )
        self.api.call(
            method=METHOD_PUT,
            url=f"fans/{self.id}",
            json={"speed_level": value},
        )

    @property
    def speed_level_pct_options(self) -> list[str]:
        """Speed level pct options."""
        return list(SPEED_LEVEL_MAP.values())

    @property
    def firmware_version(self) -> str | None:
        """Firmware version."""
        return self.data.get("firmware_version")

    @property
    def mode(self) -> str | None:
        """Mode."""
        return self.data.get("mode")

    @mode.setter
    def mode(self, value: str) -> None:
        if value not in FAN_MODES:
            _LOGGER.debug("Unable to set mode for: %s with value: %s", self.id, value)
            return
        _LOGGER.debug("Setting mode for: %s with value: %s", self.id, value)
        self.api.call(
            method=METHOD_PUT,
            url=f"fans/{self.id}",
            json={"mode": value},
        )

    @property
    def mode_options(self) -> list[str]:
        """Mode options."""
        return FAN_MODES

    def turn_off(self) -> None:
        """Turn off."""
        setattr(self, "mode", FAN_MODE_OFF)

    def turn_on(self, mode: str = FAN_MODE_ON, power_pct: int | None = None) -> None:
        """Turn on."""
        data = {"mode": mode}
        if power_pct:
            data["power"] = int(power_pct * 100)
        self.api.call(
            method=METHOD_PUT,
            url=f"fans/{self.id}",
            json=data,
        )

    def set_auto(self) -> None:
        """Set auto."""
        setattr(self, "mode", FAN_MODE_AUTO)

    def set_eco(self) -> None:
        """Set eco."""
        setattr(self, "mode", FAN_MODE_ECO)

    @property
    def size(self) -> int | None:
        """Size."""
        return self.data.get("size")

    @property
    def model_name(self) -> str:
        """Model name."""
        return MODEL_MAP.get(self.size, MODEL_UNKNOWN)

    @property
    def mqtt_username(self) -> str | None:
        """MQTT username."""
        return self.data.get("mqtt_username")

    @property
    def name(self) -> str:
        """Name."""
        if name := self.data.get("name"):
            return name
        return f"{DEFAULT_FAN_NAME} ({self.fan_id})"

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
