"""Adds config flow for SmartCocoon integration."""

import logging
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    UnitOfTime,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import SmartCocoonAPI, SmartCocoonAuthError
from .api.system import System as SmartCocoonSystem
from .const import (
    CONF_AUTHORIZATION,
    CONF_FANS,
    CONF_SAVE_RESPONSES,
    CONF_SYSTEMS,
    CONF_TIMEOUT,
    DATA_COORDINATOR,
    DEFAULT_SAVE_RESPONSES,
    DOMAIN,
    ScanInterval,
    Timeout,
)

_LOGGER = logging.getLogger(__name__)


class SmartCocoonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartCocoon integration."""

    VERSION = 1
    MINOR_VERSION = 0
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize."""
        self.api: SmartCocoonAPI = SmartCocoonAPI()
        self.index = 0
        self.response: list[SmartCocoonSystem] = []
        self.user_input: dict[str, Any] = {}

    @property
    def config_title(self) -> str:
        """Return the config title."""
        return self.user_input[CONF_EMAIL]

    async def async_step_user(self, user_input=None):
        """Async step user."""
        errors = {}

        if user_input is not None:
            self.user_input[CONF_EMAIL] = user_input[CONF_EMAIL]
            self.user_input[CONF_PASSWORD] = user_input[CONF_PASSWORD]
            self.api = SmartCocoonAPI()

            try:
                await self.api.login(
                    email=self.user_input[CONF_EMAIL],
                    password=self.user_input[CONF_PASSWORD],
                )
            except SmartCocoonAuthError:
                errors["base"] = "invalid_auth"
            except Exception as exception:
                _LOGGER.exception("%s", type(exception).__name__)
                errors["base"] = "unknown"
            else:
                _LOGGER.debug("Login successful")
                return await self.async_finish_login(errors)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.EMAIL,
                        )
                    ),
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.PASSWORD,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_finish_login(self, errors):
        """Async finish login."""
        await self.async_set_unique_id(str(self.api.user_id))
        self._abort_if_unique_id_configured()

        self.user_input[CONF_AUTHORIZATION] = self.api.authorization
        try:
            self.response = await self.api.update()
        except SmartCocoonAuthError:
            errors["base"] = "update_failed"

        return await self.async_step_systems()

    async def async_step_systems(self, user_input=None):
        """Async step systems."""
        errors = {}

        if user_input is not None:
            self.user_input[CONF_SYSTEMS] = []

            for system in self.response:
                if system.name_location in user_input[CONF_SYSTEMS]:
                    self.user_input[CONF_SYSTEMS].append(system.id)

            return await self.async_step_fans()

        system_names = [
            system.name_location for system in self.response if system.name_location
        ]

        if not system_names:
            return await self.async_step_fans()

        return self.async_show_form(
            step_id="systems",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SYSTEMS, default=system_names): SelectSelector(
                        SelectSelectorConfig(
                            options=system_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_fans(self, user_input=None):
        """Async step fans."""
        errors = {}

        if user_input is not None:
            if not self.user_input.get(CONF_FANS):
                self.user_input[CONF_FANS] = []

            for system in self.response:
                if system.id == self.user_input[CONF_SYSTEMS][self.index]:
                    for room in system.rooms:
                        for fan in room.fans:
                            if fan.name_location in user_input[CONF_FANS]:
                                self.user_input[CONF_FANS].append(fan.id)
                    self.index += 1

        if self.index == len(self.user_input[CONF_SYSTEMS]):
            self.index = 0
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(
                title=self.config_title, data=self.user_input
            )

        for system in self.response:
            if system.id == self.user_input[CONF_SYSTEMS][self.index]:
                fan_names = [
                    fan.name_location for room in system.rooms for fan in room.fans
                ]

                if not fan_names:
                    self.index += 1
                    return await self.async_step_fans()

                return self.async_show_form(
                    step_id="fans",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(CONF_FANS, default=fan_names): SelectSelector(
                                SelectSelectorConfig(
                                    options=fan_names,
                                    multiple=True,
                                    mode=SelectSelectorMode.DROPDOWN,
                                    sort=True,
                                )
                            ),
                        }
                    ),
                    description_placeholders={
                        "system_name": system.name_location or ""
                    },
                    errors=errors,
                )
        return None

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(
                title=self.config_title, data=self.user_input
            )

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SAVE_RESPONSES, default=DEFAULT_SAVE_RESPONSES
                    ): BooleanSelector(),
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=ScanInterval.DEFAULT
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=ScanInterval.MIN,
                            max=ScanInterval.MAX,
                            step=ScanInterval.STEP,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Optional(CONF_TIMEOUT, default=Timeout.DEFAULT): NumberSelector(
                        NumberSelectorConfig(
                            min=Timeout.MIN,
                            max=Timeout.MAX,
                            step=Timeout.STEP,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """SmartCocoon options callback."""
        return SmartCocoonOptionsFlowHandler()


class SmartCocoonOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for SmartCocoon."""

    def __init__(self) -> None:
        """Initialize SmartCocoon options flow."""
        self.coordinator = None
        self.coordinator_data: list[SmartCocoonSystem] = []
        self.index = 0
        self.user_input = {}

    @property
    def data(self) -> MappingProxyType[str, Any]:
        """Return the data from a config entry."""
        return self.config_entry.data

    @property
    def options(self) -> MappingProxyType[str, Any]:
        """Return the options from a config entry."""
        return self.config_entry.options

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        self.coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id][
            DATA_COORDINATOR
        ]
        self.coordinator_data = self.coordinator.data
        return await self.async_step_systems()

    async def async_step_systems(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SYSTEMS] = [
                system.id
                for system in self.coordinator_data
                if system.name_location in user_input[CONF_SYSTEMS]
            ]
            return await self.async_step_fans()

        conf_systems = [
            system.name_location
            for system in self.coordinator_data
            if system.id in self.options.get(CONF_SYSTEMS, self.data[CONF_SYSTEMS])
        ]
        system_names = [
            system.name_location
            for system in self.coordinator_data
            if system.name_location
        ]

        return self.async_show_form(
            step_id="systems",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SYSTEMS, default=conf_systems): SelectSelector(
                        SelectSelectorConfig(
                            options=system_names,
                            multiple=True,
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    ),
                }
            ),
        )

    async def async_step_fans(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            for system in self.coordinator_data:
                if system.id == self.user_input[CONF_SYSTEMS][self.index]:
                    self.user_input[CONF_FANS].extend(
                        [
                            fan.id
                            for room in system.rooms
                            for fan in room.fans
                            if fan.name_location in user_input[CONF_FANS]
                        ]
                    )
                    self.index += 1

        if self.index == len(self.user_input[CONF_SYSTEMS]):
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title="", data=self.user_input)
        if self.index == 0:
            self.user_input[CONF_FANS] = []

        for system in self.coordinator_data:
            if system.id == self.user_input[CONF_SYSTEMS][self.index]:
                conf_fans = [
                    fan.name_location
                    for room in system.rooms
                    for fan in room.fans
                    if fan.id in self.options.get(CONF_FANS, self.data[CONF_FANS])
                ]
                fan_names = [
                    fan.name_location for room in system.rooms for fan in room.fans
                ]

                return self.async_show_form(
                    step_id="fans",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(CONF_FANS, default=conf_fans): SelectSelector(
                                SelectSelectorConfig(
                                    options=fan_names,
                                    multiple=True,
                                    mode=SelectSelectorMode.DROPDOWN,
                                    sort=True,
                                )
                            ),
                        }
                    ),
                    description_placeholders={
                        "system_name": system.name_location or ""
                    },
                )
        return None

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title="", data=self.user_input)

        conf_save_responses = self.options.get(
            CONF_SAVE_RESPONSES,
            self.data.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES),
        )
        conf_scan_interval = self.options.get(
            CONF_SCAN_INTERVAL, self.data.get(CONF_SCAN_INTERVAL, ScanInterval.DEFAULT)
        )
        conf_timeout = self.options.get(
            CONF_TIMEOUT, self.data.get(CONF_TIMEOUT, Timeout.DEFAULT)
        )

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SAVE_RESPONSES, default=conf_save_responses
                    ): BooleanSelector(),
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=conf_scan_interval
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=ScanInterval.MIN,
                            max=ScanInterval.MAX,
                            step=ScanInterval.STEP,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Optional(CONF_TIMEOUT, default=conf_timeout): NumberSelector(
                        NumberSelectorConfig(
                            min=Timeout.MIN,
                            max=Timeout.MAX,
                            step=Timeout.STEP,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
        )
