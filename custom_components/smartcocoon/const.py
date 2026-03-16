"""Constants used by the SmartCocoon integration."""

from enum import IntEnum

CONF_ACCESS_TOKEN = "access_token"
CONF_AUTHORIZATION = "authorization"
CONF_CLIENT = "client"
CONF_FANS = "fans"
CONF_SAVE_RESPONSES = "save_responses"
CONF_SYSTEMS = "systems"
CONF_TIMEOUT = "timeout"

CONFIGURATION_URL = "https://mysmartcocoon.com"

DATA_COORDINATOR = "coordinator"

DOMAIN = "smartcocoon"

UNDO_UPDATE_LISTENER = "undo_update_listener"


DEFAULT_SAVE_LOCATION = f"/config/custom_components/{DOMAIN}/api/responses"
DEFAULT_SAVE_RESPONSES = False


DEVICE_MANUFACTURER = "Smart Cocoon"


class ScanInterval(IntEnum):
    """Scan interval."""

    DEFAULT = 120
    MAX = 600
    MIN = 30
    STEP = 30


class Timeout(IntEnum):
    """Timeout."""

    DEFAULT = 30
    MAX = 60
    MIN = 10
    STEP = 5
