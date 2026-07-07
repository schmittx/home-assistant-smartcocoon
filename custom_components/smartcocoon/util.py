"""Utilities for the SmartCocoon integration."""

from .const import DOMAIN


def generate_device_identifier(identifier: int | str) -> tuple[str, str]:
    """Generate device identifier."""
    return (DOMAIN, str(identifier))
