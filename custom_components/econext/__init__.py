"""The ecoNEXT integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EconextConnectionError, EconextApi
from .const import DEFAULT_PORT, DOMAIN, PLATFORMS
from .coordinator import EconextCoordinator

_LOGGER = logging.getLogger(__name__)

type EconextConfigEntry = ConfigEntry[EconextCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: EconextConfigEntry) -> bool:
    """Set up ecoNEXT from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client
    session = async_get_clientsession(hass)
    api = EconextApi(
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        session=session,
    )

    # Create coordinator
    coordinator = EconextCoordinator(hass, api)

    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except EconextConnectionError as err:
        raise ConfigEntryNotReady(f"Connection failed: {err}") from err

    # Store coordinator
    entry.runtime_data = coordinator
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "ecoNEXT integration set up for %s (%s)",
        coordinator.get_device_name(),
        coordinator.get_device_uid(),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: EconextConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
