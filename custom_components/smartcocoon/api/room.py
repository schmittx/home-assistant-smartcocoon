"""Smart Cocoon API."""

from __future__ import annotations

from .fan import Fan


class Room:
    """Room."""

    def __init__(self, api, system, data) -> None:
        """Initialize."""
        self.api = api
        self.system = system
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
    def fans(self) -> list[Fan]:
        """Fans."""
        return [
            Fan(self.api, self.system, self, fan) for fan in self.data.get("fans", [])
        ]
