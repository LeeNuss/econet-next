"""Data coordinator for ecoNET Next."""

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EconetApiError, EconetNextApi
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class EconetNextCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator to manage data updates from ecoNET device."""

    def __init__(self, hass: HomeAssistant, api: EconetNextApi) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from the API."""
        try:
            return await self.api.async_fetch_all_params()
        except EconetApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    def get_param(self, param_id: str | int) -> dict[str, Any] | None:
        """Get a parameter by ID.

        Args:
            param_id: The parameter ID (string or int).

        Returns:
            The parameter dict or None if not found.

        """
        if self.data is None:
            return None
        return self.data.get(str(param_id))

    def get_param_value(self, param_id: str | int) -> Any:
        """Get a parameter value by ID.

        Args:
            param_id: The parameter ID (string or int).

        Returns:
            The parameter value or None if not found.

        """
        param = self.get_param(param_id)
        if param is None:
            return None
        return param.get("value")

    def get_device_uid(self) -> str:
        """Get the device UID."""
        return self.get_param_value(10) or "unknown"

    def get_device_name(self) -> str:
        """Get the device name."""
        return self.get_param_value(374) or "ecoMAX"
