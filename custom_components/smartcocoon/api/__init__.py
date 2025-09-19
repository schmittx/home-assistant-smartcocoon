"""Smart Cocoon API."""

from __future__ import annotations

from collections.abc import Callable
import json
import logging
from pathlib import Path
from typing import Any

import requests

from .const import (
    API_ENDPOINT,
    LOGIN_FAILED,
    LOGIN_SUCCESS,
    LOGIN_TOO_MANY_ATTEMPTS,
    METHOD_GET,
    METHOD_POST,
    METHOD_PUT,
)
from .system import System

_LOGGER = logging.getLogger(__name__)


class SmartCocoonException(Exception):
    """SmartCocoonException."""

    def __init__(self, status_code: int, name: str, message: str) -> None:
        """Initialize."""
        super().__init__()
        self.status_code = status_code
        self.name = name
        self.message = message
        _LOGGER.debug(
            "\n- SmartCocoonException\n- Status: %s\n- Name: %s\n- Message: %s",
            self.status_code,
            self.name,
            self.message,
        )


class SmartCocoonAPI:
    """SmartCocoonAPI."""

    def __init__(
        self,
        access_token: str | None = None,
        client: str | None = None,
        save_location: str | None = None,
        uid: str | None = None,
    ) -> None:
        """Initialize."""
        self.access_token = access_token
        self.client = client
        self.save_location = save_location
        self.uid = uid

        self.credentials: dict = {}
        self.data: list = []
        self.session = requests.Session()
        self.user_id = None
        self.user_name: str = None

    def call(
        self,
        method: str,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
        **kwargs,
    ) -> dict[str, Any] | None:
        """Call."""
        if method not in (METHOD_GET, METHOD_POST, METHOD_PUT):
            return None
        if headers is None:
            headers = {}
        if params is None:
            params = {}
        if self.access_token:
            headers["access-token"] = self.access_token
        if self.client:
            headers["client"] = self.client
        if self.uid:
            headers["uid"] = self.uid
        if method == METHOD_GET:
            response = self.refresh(
                lambda: self.session.get(
                    url=f"{API_ENDPOINT}/{url}",
                    headers=headers,
                    params=params,
                    **kwargs,
                )
            )
        if method == METHOD_POST:
            response = self.refresh(
                lambda: self.session.post(
                    url=f"{API_ENDPOINT}/{url}",
                    headers=headers,
                    params=params,
                    **kwargs,
                )
            )
        if method == "put":
            response = self.refresh(
                lambda: self.session.put(
                    url=f"{API_ENDPOINT}/{url}",
                    headers=headers,
                    params=params,
                    **kwargs,
                )
            )
        response = self.parse_response(response=response)
        self.save_response(response=response, name=url)
        return response

    def login(self, email: str, password: str) -> str:
        """Login."""
        try:
            data = {"email": email, "password": password}
            response = self.call(
                method=METHOD_POST,
                url="auth/sign_in",
                data=data,
            )
            self.user_id = response["data"]["id"]
        except SmartCocoonException as exception:
            if all(
                [
                    exception.status_code == 401,
                    exception.message == "Login Failed",
                ]
            ):
                return LOGIN_FAILED
            if all(
                [
                    exception.status_code == 403,
                    exception.message == "Too many failed attempts",
                ]
            ):
                return LOGIN_TOO_MANY_ATTEMPTS
            return LOGIN_FAILED
        self.credentials = data
        return LOGIN_SUCCESS

    def parse_response(self, response: requests.Response) -> dict[str, Any] | None:
        """Parse response."""
        text = json.loads(response.text)
        if response.status_code not in [200]:
            error = text["error"]
            raise SmartCocoonException(
                status_code=error.get("statusCode"),
                name=error.get("name"),
                message=error.get("message"),
            )
        self.access_token = response.headers["access-token"]
        self.client = response.headers["client"]
        self.uid = response.headers["uid"]
        return text

    def refresh(self, function: Callable) -> requests.Response:
        """Refresh."""
        response = function()
        if response.status_code not in [200]:
            text = json.loads(response.text)
            error = text["error"]
            if all(
                [
                    response.status_code == 401,
                    error["message"] == "Invalid Access Token",
                ]
            ):
                self.login(
                    email=self.credentials["email"],
                    password=self.credentials["password"],
                )
                response = function()
        return response

    def save_response(self, response: dict[str, Any], name: str = "response"):
        """Save response."""
        if self.save_location and response:
            if not Path(self.save_location).is_dir():
                _LOGGER.debug("Creating directory: %s", self.save_location)
                Path(self.save_location).mkdir()
            file_path_name = f"{self.save_location}/{name}.json"
            _LOGGER.debug("Saving response: %s", file_path_name)
            with Path(file_path_name).open(mode="w", encoding="utf-8") as file:
                json.dump(
                    obj=response,
                    fp=file,
                    indent=4,
                    default=lambda o: "not-serializable",
                    sort_keys=True,
                )
            file.close()

    def update(self, target_systems: list[int] | None = None) -> list[System]:
        """Update."""
        try:
            data = []
            systems = self.call(
                method=METHOD_GET,
                url="client_systems",
            )
            for system in systems["client_systems"]:
                if any(
                    [
                        target_systems is None,
                        target_systems and system["id"] in target_systems,
                    ]
                ):
                    rooms = self.call(
                        method=METHOD_GET,
                        url="rooms",
                        params={
                            "filter%5Bthermostat%5D%5Bclient_system_id": system["id"],
                        },
                    )
                    system["rooms"] = rooms["rooms"]
                    data.append(System(self, system))
            self.data = data
        except SmartCocoonException:
            return self.data
        return self.data
