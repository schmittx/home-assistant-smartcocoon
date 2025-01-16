"""Support for SmartCocoon fan entities."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.fan import (
    FanEntity,
    FanEntityDescription,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartCocoonEntity
from .api.const import FAN_MODE_AUTO, FAN_MODE_ECO
from .const import (
    CONF_FANS,
    CONF_SYSTEMS,
    DATA_COORDINATOR,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

@dataclass
class SmartCocoonFanEntityDescription(FanEntityDescription):
    """Class to describe a SmartCocoon fan entity."""

    translation_key: str | None = "all"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a SmartCocoon fan entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[SmartCocoonFanEntity] = []

    for system in coordinator.data:
        if system.id in entry[CONF_SYSTEMS]:
            for room in system.rooms:
                for fan in room.fans:
                    if fan.id in entry[CONF_FANS]:
                        entities.append(
                            SmartCocoonFanEntity(
                                coordinator=coordinator,
                                system_id=system.id,
                                room_id=room.id,
                                fan_id=fan.id,
                                entity_description=SmartCocoonFanEntityDescription(
                                    key=None,
                                    name=None,
                                ),
                            )
                        )

    async_add_entities(entities)


class SmartCocoonFanEntity(FanEntity, SmartCocoonEntity):
    """Representation of a SmartCocoon fan entity."""

    entity_description: SmartCocoonFanEntityDescription
    _attr_preset_modes: list[str] | None = []

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self.fan.fan_on

    @property
    def percentage(self) -> int:
        """Return the current speed percentage."""
        return self.fan.power_pct

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return 100

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode, e.g., auto, smart, interval, favorite."""
        return self.fan.mode

    @property
    def preset_modes(self) -> list[str]:
        """List of available preset modes."""
        return [FAN_MODE_AUTO, FAN_MODE_ECO]

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        supported_features = FanEntityFeature(0)
        supported_features |= FanEntityFeature.SET_SPEED
        supported_features |= FanEntityFeature.TURN_OFF
        supported_features |= FanEntityFeature.TURN_ON
        supported_features |= FanEntityFeature.PRESET_MODE
        return supported_features

    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the entity on."""
        self.fan.turn_on(power_pct=percentage)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the entity on."""
        await super().async_turn_on(percentage, preset_mode, **kwargs)
        await self.coordinator.async_request_refresh()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self.fan.turn_off()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await super().async_turn_off(**kwargs)
        await self.coordinator.async_request_refresh()

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        self.fan.set_power_pct(percentage)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        await super().async_set_percentage(percentage)
        await self.coordinator.async_request_refresh()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self.preset_modes:
            _LOGGER.warning(f"Invalid preset mode: {preset_mode}")
        self.fan.set_auto() if preset_mode == FAN_MODE_AUTO else self.fan.set_eco()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        await super().async_set_preset_mode(preset_mode)
        await self.coordinator.async_request_refresh()
