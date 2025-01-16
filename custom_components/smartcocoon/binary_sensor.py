"""Support for SmartCocoon binary sensor entities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartCocoonEntity
from .const import (
    CONF_FANS,
    CONF_SYSTEMS,
    DATA_COORDINATOR,
    DOMAIN,
)

@dataclass
class SmartCocoonBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class to describe a SmartCocoon binary sensor entity."""

    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC


BINARY_SENSOR_DESCRIPTIONS: list[SmartCocoonBinarySensorEntityDescription] = [
    SmartCocoonBinarySensorEntityDescription(
        key="fan_on",
        name="Fan Active",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a SmartCocoon binary sensor entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[SmartCocoonBinarySensorEntity] = []

    for system in coordinator.data:
        if system.id in entry[CONF_SYSTEMS]:
            for room in system.rooms:
                for fan in room.fans:
                    if fan.id in entry[CONF_FANS]:
                        for description in BINARY_SENSOR_DESCRIPTIONS:
                            if hasattr(fan, description.key):
                                entities.append(
                                    SmartCocoonBinarySensorEntity(
                                        coordinator=coordinator,
                                        system_id=system.id,
                                        room_id=room.id,
                                        fan_id=fan.id,
                                        entity_description=description,
                                    )
                                )

    async_add_entities(entities)


class SmartCocoonBinarySensorEntity(BinarySensorEntity, SmartCocoonEntity):
    """Representation of a SmartCocoon binary sensor entity."""

    entity_description: SmartCocoonBinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return getattr(self.fan, self.entity_description.key)
