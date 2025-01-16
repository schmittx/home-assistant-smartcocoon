"""Smart Cocoon API"""
API_ENDPOINT = "https://app.mysmartcocoon.com/api"

LOGIN_FAILED = "login_failed"
LOGIN_SUCCESS = "login_success"
LOGIN_TOO_MANY_ATTEMPTS = "login_too_many_attempts"

METHOD_GET = "get"
METHOD_POST = "post"
METHOD_PUT = "put"

MODEL_3_X_10 = '3"x10"'
MODEL_4_X_10 = '4"x10"'
MODEL_UNKNOWN = "Unknown"

MODEL_MAP = {
    3: MODEL_3_X_10,
    4: MODEL_4_X_10,
}

FAN_MODE_AUTO = "auto"
FAN_MODE_ECO = "eco"
FAN_MODE_OFF = "always_off"
FAN_MODE_ON = "always_on"

FAN_MODES = [
    FAN_MODE_AUTO,
    FAN_MODE_ECO,
    FAN_MODE_OFF,
    FAN_MODE_ON,
]

SPEED_LEVEL_8 = "8_pct"
SPEED_LEVEL_16 = "16_pct"
SPEED_LEVEL_25 = "25_pct"
SPEED_LEVEL_33 = "33_pct"
SPEED_LEVEL_41 = "41_pct"
SPEED_LEVEL_50 = "50_pct"
SPEED_LEVEL_58 = "58_pct"
SPEED_LEVEL_66 = "66_pct"
SPEED_LEVEL_75 = "75_pct"
SPEED_LEVEL_83 = "83_pct"
SPEED_LEVEL_91 = "91_pct"
SPEED_LEVEL_100 = "100_pct"
SPEED_LEVEL_UNKNOWN = "unknown"

SPEED_LEVEL_MAP = {
    1: SPEED_LEVEL_8,
    2: SPEED_LEVEL_16,
    3: SPEED_LEVEL_25,
    4: SPEED_LEVEL_33,
    5: SPEED_LEVEL_41,
    6: SPEED_LEVEL_50,
    7: SPEED_LEVEL_58,
    8: SPEED_LEVEL_66,
    9: SPEED_LEVEL_75,
    10: SPEED_LEVEL_83,
    11: SPEED_LEVEL_91,
    12: SPEED_LEVEL_100,
}
