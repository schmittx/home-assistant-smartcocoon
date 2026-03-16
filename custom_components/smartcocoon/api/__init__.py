"""Smart Cocoon API."""

from __future__ import annotations

from http import HTTPMethod
import json
import logging
from pathlib import Path
from typing import Any, Literal

import aiofiles
import aiohttp

from .const import API_PREFIX
from .system import System

_LOGGER = logging.getLogger(__name__)


class SmartCocoonAuthError(Exception):
    """Exception to indicate an authentication error."""


class SmartCocoonAPI:
    """SmartCocoonAPI."""

    def __init__(
        self,
        authorization: str | None = None,
        save_location: str | None = None,
    ) -> None:
        """Initialize."""
        self.authorization = authorization
        self.save_location = save_location
        self.user_id = None

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Login."""
        path = "auth/sign_in"
        data = {"email": email, "password": password}
        async with aiohttp.request(
            method=HTTPMethod.POST, url=f"{API_PREFIX}/{path}", data=data
        ) as response:
            if response.status == 403:
                raise SmartCocoonAuthError
            response.raise_for_status()
            result = await self.save_result(result=await response.json(), name=path)
            self.authorization = response.headers.get("authorization")
            self.user_id = result["data"]["id"]
            return result

    async def call(
        self,
        method: Literal[HTTPMethod.GET, HTTPMethod.POST, HTTPMethod.PUT],
        path: str,
        params: dict | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Call."""
        async with aiohttp.request(
            method=method,
            url=f"{API_PREFIX}/{path}",
            headers={"authorization": self.authorization} if self.authorization else {},
            params=params,
            **kwargs,
        ) as response:
            if response.status == 403:
                raise SmartCocoonAuthError
            response.raise_for_status()
            if response.status == 204:
                return None
            return await self.save_result(result=await response.json(), name=path)

    async def save_result(
        self, result: dict[str, Any], name: str = "result"
    ) -> dict[str, Any]:
        """Save the result to a file."""
        if self.save_location and result:
            if not Path(self.save_location).is_dir():
                _LOGGER.debug("Creating directory: %s", self.save_location)
                Path(self.save_location).mkdir()
            name = name.replace("/", "_").replace(".", "_")
            file_path_name = f"{self.save_location}/{name}.json"
            _LOGGER.debug("Saving result: %s", file_path_name)
            async with aiofiles.open(file_path_name, mode="w") as file:
                await file.write(
                    json.dumps(
                        result,
                        default=lambda o: "not-serializable",
                        indent=4,
                        sort_keys=True,
                    )
                )
        return result

    async def update(self, target_systems: list[int] | None = None) -> list[System]:
        """Update."""
        data = []
        systems = await self.call(
            method=HTTPMethod.GET,
            path="client_systems",
        )
        if systems:
            for system in systems["client_systems"]:
                if any(
                    [
                        target_systems is None,
                        target_systems and system["id"] in target_systems,
                    ]
                ):
                    rooms = await self.call(
                        method=HTTPMethod.GET,
                        path="rooms",
                        params={
                            "filter%5Bthermostat%5D%5Bclient_system_id": system["id"],
                        },
                    )
                    if rooms:
                        system["rooms"] = rooms["rooms"]
                        data.append(System(self, system))
        return data
