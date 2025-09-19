"""The SmartCocoon integration."""

from __future__ import annotations

from asyncio import timeout
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import SmartCocoonAPI, SmartCocoonException
from .api.fan import Fan as SmartCocoonFan
from .api.room import Room as SmartCocoonRoom
from .api.system import System as SmartCocoonSystem
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT,
    CONF_FANS,
    CONF_SAVE_RESPONSES,
    CONF_SYSTEMS,
    CONF_TIMEOUT,
    CONFIGURATION_URL,
    DATA_COORDINATOR,
    DEFAULT_SAVE_LOCATION,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEVICE_MANUFACTURER,
    DOMAIN,
    UNDO_UPDATE_LISTENER,
)

PLATFORMS = (
    Platform.BINARY_SENSOR,
    Platform.FAN,
    Platform.SELECT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    data = config_entry.data
    options = config_entry.options

    conf_systems = options.get(CONF_SYSTEMS, data.get(CONF_SYSTEMS, []))
    conf_fans = options.get(CONF_FANS, data.get(CONF_FANS, []))
    conf_identifiers = [(DOMAIN, conf_id) for conf_id in conf_systems + conf_fans]

    device_registry = dr.async_get(hass)
    device_entries = dr.async_entries_for_config_entry(
        registry=device_registry,
        config_entry_id=config_entry.entry_id,
    )
    for device_entry in device_entries:
        orphan_identifiers = [
            bool(device_identifier not in conf_identifiers)
            for device_identifier in device_entry.identifiers
        ]
        if all(orphan_identifiers):
            device_registry.async_remove_device(device_entry.id)

    api = SmartCocoonAPI(
        access_token=data[CONF_ACCESS_TOKEN],
        client=data[CONF_CLIENT],
        save_location=DEFAULT_SAVE_LOCATION
        if options.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES)
        else None,
        uid=data[CONF_EMAIL],
    )

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            async with timeout(
                options.get(CONF_TIMEOUT, data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))
            ):
                return await hass.async_add_executor_job(api.update, conf_systems)
        except SmartCocoonException as exception:
            raise UpdateFailed(
                "Error communicating with API, Status: {}, Error Name: {}, Error Message: {}"
            ).format(
                exception.status_code,
                exception.name,
                exception.message,
            ) from exception

    coordinator = DataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name=f"SmartCocoon ({data[CONF_EMAIL]})",
        update_method=async_update_data,
        update_interval=timedelta(
            seconds=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ),
    )
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        CONF_SYSTEMS: conf_systems,
        CONF_FANS: conf_fans,
        DATA_COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: config_entry.add_update_listener(async_update_listener),
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry=config_entry,
        platforms=PLATFORMS,
    )
    if unload_ok:
        hass.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class SmartCocoonEntity(CoordinatorEntity):
    """Representation of a SmartCocoon entity."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        system_id: int,
        room_id: int,
        fan_id: int,
        entity_description: EntityDescription = None,
    ) -> None:
        """Initialize the device."""
        super().__init__(coordinator)
        self.system_id = system_id
        self.room_id = room_id
        self.fan_id = fan_id
        self.entity_description = entity_description

    @property
    def system(self) -> SmartCocoonSystem | None:
        """Return a SmartCocoonSystem object."""
        systems = {system.id: system for system in self.coordinator.data}
        return systems.get(self.system_id)

    @property
    def room(self) -> SmartCocoonRoom | None:
        """Return a SmartCocoonRoom object."""
        rooms = {room.id: room for room in self.system.rooms}
        return rooms.get(self.room_id)

    @property
    def fan(self) -> SmartCocoonFan | None:
        """Return a SmartCocoonFan object."""
        fans = {fan.id: fan for fan in self.room.fans}
        return fans.get(self.fan_id)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return all(
            [
                super().available,
                self.fan.connected,
            ]
        )

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        return dr.DeviceInfo(
            configuration_url=CONFIGURATION_URL,
            hw_version=self.fan.fan_id,
            identifiers={(DOMAIN, self.fan.id)},
            manufacturer=DEVICE_MANUFACTURER,
            model=self.fan.model_name,
            name=self.fan.name,
            suggested_area=self.room.name,
            sw_version=self.fan.firmware_version,
        )

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        name = self.device_info["name"]
        if description := self.entity_description.name:
            return f"{name} {description}"
        return name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        unique_id = self.fan.fan_id
        if key := self.entity_description.key:
            return f"{unique_id}-{key}"
        return unique_id
