"""Smart Cocoon API"""
from __future__ import annotations

from typing import Any

from .room import Room


class System(object):

    def __init__(self, api, data):
        self.api = api
        self.data = data

    @property
    def id(self) -> int | None:
        return self.data.get("id")

    @property
    def name(self) -> str | None:
        return self.data.get("name")

    @property
    def name_location(self) -> str:
        return f"{self.name} ({self.location_city}, {self.location_state})"

    @property
    def user_id(self) -> int | None:
        return self.data.get("user_id")

    @property
    def location(self) -> dict[str, Any]:
        return self.data.get("location", {})

    @property
    def location_id(self) -> int | None:
        return self.location.get("id")

    @property
    def location_street(self) -> str | None:
        return self.location.get("street")

    @property
    def location_city(self) -> str | None:
        return self.location.get("city")

    @property
    def location_state(self) -> str | None:
        return self.location.get("state")

    @property
    def location_country(self) -> str | None:
        return self.location.get("country")

    @property
    def location_postal_code(self) -> str | None:
        return self.location.get("postal_code")

    @property
    def rooms(self) -> list[Room]:
        return [Room(self.api, self, room) for room in self.data.get("rooms", [])]
