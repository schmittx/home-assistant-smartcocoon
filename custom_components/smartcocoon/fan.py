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
from .api.const import FanMode
from .const import CONF_FANS, CONF_SYSTEMS, DATA_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
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
                entities.extend(
                    SmartCocoonFanEntity(
                        coordinator=coordinator,
                        system_id=system.id,
                        room_id=room.id,
                        fan_id=fan.id,
                        entity_description=SmartCocoonFanEntityDescription(
                            key="fan",
                            name=None,
                        ),
                    )
                    for fan in room.fans
                    if fan.id in entry[CONF_FANS]
                )

    async_add_entities(entities)


class SmartCocoonFanEntity(FanEntity, SmartCocoonEntity):
    """Representation of a SmartCocoon fan entity."""

    entity_description: SmartCocoonFanEntityDescription
    _attr_preset_modes: list[str] | None = []

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self.fan and self.fan.fan_on

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode, e.g., auto, smart, interval, favorite."""
        if self.fan:
            return self.fan.mode
        return None

    @property
    def preset_modes(self) -> list[str]:
        """List of available preset modes."""
        return [FanMode.AUTO, FanMode.ECO]

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        supported_features = FanEntityFeature(0)
        supported_features |= FanEntityFeature.TURN_OFF
        supported_features |= FanEntityFeature.TURN_ON
        supported_features |= FanEntityFeature.PRESET_MODE
        return supported_features

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the entity on."""
        if self.fan:
            await self.fan.turn_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        if self.fan:
            await self.fan.turn_off()
            await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self.preset_modes:
            _LOGGER.warning("Invalid preset mode: %s", preset_mode)
        if self.fan:
            await self.fan.set_mode(mode=preset_mode)
            await self.coordinator.async_request_refresh()
