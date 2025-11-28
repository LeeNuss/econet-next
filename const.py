"""Constants for the ecoNET Next integration."""

DOMAIN = "econet_next"

# Platforms to set up
PLATFORMS: list[str] = []

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Default values
DEFAULT_PORT = 8080

# API endpoints
API_ENDPOINT_ALL_PARAMS = "/econet/allParams"
API_ENDPOINT_NEW_PARAM = "/econet/newParam"

# Update interval in seconds
UPDATE_INTERVAL = 30

# Device info
MANUFACTURER = "Plum"
