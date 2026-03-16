"""Smart Cocoon API."""

from enum import StrEnum


class FanMode(StrEnum):
    """Fan mode."""

    AUTO = "auto"
    ECO = "eco"
    OFF = "always_off"
    ON = "always_on"


class DeviceSize(StrEnum):
    """Device size."""

    THREE_INCH = '3"x10"'
    FOUR_INCH = '4"x10"'


API_PREFIX = "https://app.mysmartcocoon.com/api"

DEFAULT_MODEL_NAME = "Smart Vent / Register Booster Fan"

DEVICE_SIZE_MAP = {
    3: DeviceSize.THREE_INCH,
    4: DeviceSize.FOUR_INCH,
}
