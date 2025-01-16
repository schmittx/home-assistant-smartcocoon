"""Adds config flow for SmartCocoon integration."""
import logging
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.const import (
    UnitOfTime,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
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

from .api import LOGIN_SUCCESS, SmartCocoonAPI, SmartCocoonException
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT,
    CONF_FANS,
    CONF_SAVE_RESPONSES,
    CONF_SYSTEMS,
    CONF_TIMEOUT,
    DATA_COORDINATOR,
    DEFAULT_SAVE_RESPONSES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MAX_TIMEOUT,
    MIN_SCAN_INTERVAL,
    MIN_TIMEOUT,
    STEP_SCAN_INTERVAL,
    STEP_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class SmartCocoonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SmartCocoon integration."""

    VERSION = 1
    MINOR_VERSION = 0
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self.api = None
        self.index = 0
        self.response = None
        self.user_input = {}

    @property
    def config_title(self) -> str:
        """Return the config title."""
        return self.user_input[CONF_EMAIL]

    async def async_finish_login(self, errors):
        await self.async_set_unique_id(str(self.api.user_id))
        self._abort_if_unique_id_configured()

        try:
            self.response = await self.hass.async_add_executor_job(self.api.update)
        except SmartCocoonException as exception:
            errors["base"] = "update_failed"

        self.user_input[CONF_ACCESS_TOKEN] = self.api.access_token
        self.user_input[CONF_CLIENT] = self.api.client

        return await self.async_step_systems()

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:

            self.user_input[CONF_EMAIL] = user_input[CONF_EMAIL]
            self.user_input[CONF_PASSWORD] = user_input[CONF_PASSWORD]
            self.api = SmartCocoonAPI()

            result = await self.hass.async_add_executor_job(
                self.api.login,
                self.user_input[CONF_EMAIL],
                self.user_input[CONF_PASSWORD],
            )

            if result == LOGIN_SUCCESS:
                _LOGGER.debug(f"Login successful")
                return await self.async_finish_login(errors)
            errors["base"] = result

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

    async def async_step_systems(self, user_input=None):
        errors = {}

        if user_input is not None:

            self.user_input[CONF_SYSTEMS] = []

            for system in self.response:
                if system.name_location in user_input[CONF_SYSTEMS]:
                    self.user_input[CONF_SYSTEMS].append(system.id)

            return await self.async_step_fans()

        system_names = [system.name_location for system in self.response]

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
        errors = {}

        if user_input is not None:

            if not self.user_input.get(CONF_FANS):
                self.user_input[CONF_FANS] = []

            for system in self.response:
                if system.id == self.user_input[CONF_SYSTEMS][self.index]:
                    for room in system.rooms:
                        for fan in room.fans:
                            if fan.fan_id_location in user_input[CONF_FANS]:
                                self.user_input[CONF_FANS].append(fan.id)
                    self.index += 1

        if self.index == len(self.user_input[CONF_SYSTEMS]):
            self.index = 0
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title=self.config_title, data=self.user_input)

        for system in self.response:
            if system.id == self.user_input[CONF_SYSTEMS][self.index]:
                fan_names = [fan.fan_id_location for room in system.rooms for fan in room.fans]

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
                    description_placeholders={"system_name": system.name_location},
                    errors=errors,
                )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title=self.config_title, data=self.user_input)

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SAVE_RESPONSES, default=DEFAULT_SAVE_RESPONSES): BooleanSelector(),
                    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=STEP_SCAN_INTERVAL,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_TIMEOUT,
                            max=MAX_TIMEOUT,
                            step=STEP_TIMEOUT,
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

    def __init__(self):
        """Initialize SmartCocoon options flow."""
        self.coordinator = None
        self.index = 0
        self.user_input = {}

    @property
    def data(self) -> dict[str, Any]:
        """Return the data from a config entry."""
        return self.config_entry.data

    @property
    def options(self) -> dict[str, Any]:
        """Return the options from a config entry."""
        return self.config_entry.options

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        self.coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id][DATA_COORDINATOR]
        return await self.async_step_systems()

    async def async_step_systems(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SYSTEMS] = [system.id for system in self.coordinator.data if system.name_location in user_input[CONF_SYSTEMS]]
            return await self.async_step_fans()

        conf_systems = [system.name_location for system in self.coordinator.data if system.id in self.options.get(CONF_SYSTEMS, self.data[CONF_SYSTEMS])]
        system_names = [system.name_location for system in self.coordinator.data]

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
            for system in self.coordinator.data:
                if system.id == self.user_input[CONF_SYSTEMS][self.index]:
                    self.user_input[CONF_FANS].extend([fan.id for room in system.rooms for fan in room.fans if fan.fan_id_location in user_input[CONF_FANS]])
                    self.index += 1

        if self.index == len(self.user_input[CONF_SYSTEMS]):
            if self.show_advanced_options:
                return await self.async_step_advanced()
            return self.async_create_entry(title="", data=self.user_input)
        elif self.index == 0:
            self.user_input[CONF_FANS] = []

        for system in self.coordinator.data:
            if system.id == self.user_input[CONF_SYSTEMS][self.index]:
                conf_fans = [fan.fan_id_location for room in system.rooms for fan in room.fans if fan.id in self.options.get(CONF_FANS, self.data[CONF_FANS])]
                fan_names = [fan.fan_id_location for room in system.rooms for fan in room.fans]

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
                    description_placeholders={"system_name": system.name_location},
                )

    async def async_step_advanced(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.user_input[CONF_SAVE_RESPONSES] = user_input[CONF_SAVE_RESPONSES]
            self.user_input[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.user_input[CONF_TIMEOUT] = user_input[CONF_TIMEOUT]
            return self.async_create_entry(title="", data=self.user_input)

        conf_save_responses = self.options.get(CONF_SAVE_RESPONSES, self.data.get(CONF_SAVE_RESPONSES, DEFAULT_SAVE_RESPONSES))
        conf_scan_interval = self.options.get(CONF_SCAN_INTERVAL, self.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        conf_timeout = self.options.get(CONF_TIMEOUT, self.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))

        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SAVE_RESPONSES, default=conf_save_responses): BooleanSelector(),
                    vol.Optional(CONF_SCAN_INTERVAL, default=conf_scan_interval): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=STEP_SCAN_INTERVAL,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                    vol.Optional(CONF_TIMEOUT, default=conf_timeout): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_TIMEOUT,
                            max=MAX_TIMEOUT,
                            step=STEP_TIMEOUT,
                            unit_of_measurement=UnitOfTime.SECONDS,
                        )
                    ),
                }
            ),
        )
