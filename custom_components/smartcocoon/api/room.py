"""Smart Cocoon API"""
from __future__ import annotations

from .fan import Fan


class Room(object):

    def __init__(self, api, system, data):
        self.api = api
        self.system = system
        self.data = data

    @property
    def id(self) -> int | None:
        return self.data.get("id")

    @property
    def name(self) -> str | None:
        return self.data.get("name")

    @property
    def fans(self) -> list[Fan]:
        return [Fan(self.api, self.system, self, fan) for fan in self.data.get("fans", [])]
