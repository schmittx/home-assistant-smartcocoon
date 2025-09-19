"""Smart Cocoon API."""

from __future__ import annotations

from typing import Any

from .room import Room


class System:
    """System."""

    def __init__(self, api, data) -> None:
        """Initialize."""
        self.api = api
        self.data = data

    @property
    def id(self) -> int | None:
        """ID."""
        return self.data.get("id")

    @property
    def name(self) -> str | None:
        """Name."""
        return self.data.get("name")

    @property
    def name_location(self) -> str:
        """Name location."""
        if self.location_city and self.location_state:
            return f"{self.name} ({self.location_city}, {self.location_state})"
        if self.location_postal_code:
            return f"{self.name} ({self.location_postal_code})"
        return self.name

    @property
    def user_id(self) -> int | None:
        """User ID."""
        return self.data.get("user_id")

    @property
    def location(self) -> dict[str, Any]:
        """Location."""
        return self.data.get("location", {})

    @property
    def location_id(self) -> int | None:
        """Location ID."""
        return self.location.get("id")

    @property
    def location_street(self) -> str | None:
        """Location street."""
        return self.location.get("street")

    @property
    def location_city(self) -> str | None:
        """Location city."""
        return self.location.get("city")

    @property
    def location_state(self) -> str | None:
        """Location state."""
        return self.location.get("state")

    @property
    def location_country(self) -> str | None:
        """Location country."""
        return self.location.get("country")

    @property
    def location_postal_code(self) -> str | None:
        """Location postal code."""
        return self.location.get("postal_code")

    @property
    def rooms(self) -> list[Room]:
        """Location rooms."""
        return [Room(self.api, self, room) for room in self.data.get("rooms", [])]
