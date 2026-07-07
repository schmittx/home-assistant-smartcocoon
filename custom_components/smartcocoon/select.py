"""Support for SmartCocoon select entities."""

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SmartCocoonEntity
from .const import CONF_FANS, CONF_SYSTEMS, DATA_COORDINATOR, DOMAIN


@dataclass(frozen=True)
class SmartCocoonSelectEntityDescription(SelectEntityDescription):
    """Class to describe a SmartCocoon select entity."""

    entity_category: EntityCategory | None = EntityCategory.CONFIG
    options_key: str | None = None
    translation_key: str | None = "all"


SELECT_DESCRIPTIONS: list[SmartCocoonSelectEntityDescription] = [
    SmartCocoonSelectEntityDescription(
        key="mode",
        name="Mode",
        options_key="mode_options",
        icon="mdi:list-box",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a SmartCocoon select entity based on a config entry."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[SmartCocoonSelectEntity] = []

    for system in coordinator.data:
        if system.id in entry[CONF_SYSTEMS]:
            for room in system.rooms:
                for fan in room.fans:
                    if fan.id in entry[CONF_FANS]:
                        entities.extend(
                            SmartCocoonSelectEntity(
                                coordinator=coordinator,
                                system_id=system.id,
                                room_id=room.id,
                                fan_id=fan.id,
                                entity_description=description,
                            )
                            for description in SELECT_DESCRIPTIONS
                            if hasattr(fan, description.key)
                        )

    async_add_entities(entities)


class SmartCocoonSelectEntity(SelectEntity, SmartCocoonEntity):
    """Representation of a SmartCocoon select entity."""

    entity_description: SmartCocoonSelectEntityDescription

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        if self.entity_description.options_key:
            return getattr(self.fan, self.entity_description.options_key)
        return []

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return getattr(self.fan, self.entity_description.key)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self.fan:
            await self.fan.set_property(self.entity_description.key, option)
            await self.coordinator.async_request_refresh()
