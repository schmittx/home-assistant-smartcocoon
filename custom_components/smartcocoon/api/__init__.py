"""Smart Cocoon API"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import json
import logging
import os
import requests

from .system import System
from .const import (
    API_ENDPOINT,
    LOGIN_FAILED,
    LOGIN_SUCCESS,
    LOGIN_TOO_MANY_ATTEMPTS,
    METHOD_GET,
    METHOD_POST,
    METHOD_PUT,
)

_LOGGER = logging.getLogger(__name__)


class SmartCocoonException(Exception):
    def __init__(self, status_code: int, name: str, message: str) -> None:
        super(SmartCocoonException, self).__init__()
        self.status_code = status_code
        self.name = name
        self.message = message
        _LOGGER.debug(f"\n- SmartCocoonException\n- Status: {self.status_code}\n- Name: {self.name}\n- Message: {self.message}")


class SmartCocoonAPI(object):

    def __init__(
            self,
            access_token: str = None,
            client: str = None,
            save_location: str = None,
            uid: str = None,
        ) -> None:
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
            headers: dict = {},
            params: dict = {},
            **kwargs,
        ) -> dict[str, Any] | None:
        if method not in (METHOD_GET, METHOD_POST, METHOD_PUT):
            return
        if self.access_token:
            headers["access-token"] = self.access_token
        if self.client:
            headers["client"] = self.client
        if self.uid:
            headers["uid"] = self.uid
        if method == METHOD_GET:
            response = self.refresh(lambda:
                self.session.get(
                    url=f"{API_ENDPOINT}/{url}",
                    headers=headers,
                    params=params,
                    **kwargs,
                )
            )
        if method == METHOD_POST:
            response = self.refresh(lambda:
                self.session.post(
                    url=f"{API_ENDPOINT}/{url}",
                    headers=headers,
                    params=params,
                    **kwargs,
                )
            )
        if method == "put":
            response = self.refresh(lambda:
                self.session.put(
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
            elif all(
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
        text = json.loads(response.text)
        return text

    def refresh(self, function: Callable) -> requests.Response:
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
        if self.save_location and response:
            if not os.path.isdir(self.save_location):
                os.mkdir(self.save_location)
            name = name.replace("/", "_").replace(".", "_")
            with open(f"{self.save_location}/{name}.json", "w") as file:
                json.dump(
                    obj=response,
                    fp=file,
                    indent=4,
                    default=lambda o: "not-serializable",
                    sort_keys=True,
                )
            file.close()

    def update(self, target_systems: list[int] | None = None) -> list[System]:
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
                        url=f"rooms",
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
