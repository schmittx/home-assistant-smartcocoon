"""Support for SmartCocoon number entities."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartCocoonEntity
from .const import CONF_FANS, CONF_SYSTEMS, DATA_COORDINATOR, DOMAIN


@dataclass(frozen=True)
class SmartCocoonNumberEntityDescription(NumberEntityDescription):
    """Class to describe a SmartCocoon number entity."""

    entity_category: EntityCategory | None = EntityCategory.CONFIG
    native_max_value: float = 100
    native_min_value: float = 1
    native_step: float = 1
    translation_key: str | None = "all"


NUMBER_DESCRIPTIONS: list[SmartCocoonNumberEntityDescription] = [
    SmartCocoonNumberEntityDescription(
        key="speed_level",
        name="Speed Level",
        device_class=NumberDeviceClass.POWER_FACTOR,
        native_max_value=12,
        native_unit_of_measurement=None,
        icon="mdi:speedometer",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a SmartCocoon number entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[SmartCocoonNumberEntity] = []

    for system in coordinator.data:
        if system.id in entry[CONF_SYSTEMS]:
            for room in system.rooms:
                for fan in room.fans:
                    if fan.id in entry[CONF_FANS]:
                        entities.extend(
                            SmartCocoonNumberEntity(
                                coordinator=coordinator,
                                system_id=system.id,
                                room_id=room.id,
                                fan_id=fan.id,
                                entity_description=description,
                            )
                            for description in NUMBER_DESCRIPTIONS
                            if hasattr(fan, description.key)
                        )

    async_add_entities(entities)


class SmartCocoonNumberEntity(NumberEntity, SmartCocoonEntity):
    """Representation of a SmartCocoon number entity."""

    entity_description: SmartCocoonNumberEntityDescription

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        return getattr(self.fan, self.entity_description.key)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        if self.fan:
            await self.fan.set_property(self.entity_description.key, value)
            await self.coordinator.async_request_refresh()
