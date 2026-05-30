"""Constants for the homepilot integration."""

DOMAIN = "homepilot"
DEFAULT_PORT = 80
SCAN_INTERVAL = 30  # seconds

API_DEVICES = "/deviceajax.do?devices=1"

CMD_UP = "MoveUp"
CMD_DOWN = "MoveDown"
CMD_STOP = "Stop"
CMD_POSITION = "MoveToPosition"

# Homepilot deviceGroup 2 = roller shutters/covers
DEVICE_GROUP_COVER = 2
