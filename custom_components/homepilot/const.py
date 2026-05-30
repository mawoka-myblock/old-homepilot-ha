"""Constants for the homepilot integration."""

DOMAIN = "homepilot"
DEFAULT_PORT = 80
SCAN_INTERVAL = 30  # seconds

API_DEVICES = "/deviceajax.do?devices=1"

CID_OPEN = 1
CID_STOP = 2
CID_CLOSE = 3
CID_POSITION = 9

# Homepilot deviceGroup 2 = roller shutters/covers
DEVICE_GROUP_COVER = 2
