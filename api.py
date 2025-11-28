"""API client for ecoNET Next."""

import json
import logging
from typing import Any

import aiohttp
from aiohttp import BasicAuth

from .const import API_ENDPOINT_ALL_PARAMS, API_ENDPOINT_NEW_PARAM

_LOGGER = logging.getLogger(__name__)


class EconetApiError(Exception):
    """Base exception for API errors."""


class EconetAuthError(EconetApiError):
    """Authentication error."""


class EconetConnectionError(EconetApiError):
    """Connection error."""


class EconetNextApi:
    """API client for ecoNET devices using allParams endpoint."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._port = port
        self._auth = BasicAuth(username, password)
        self._session = session
        self._base_url = f"http://{host}:{port}"

    @property
    def host(self) -> str:
        """Return the host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port."""
        return self._port

    async def async_fetch_all_params(self) -> dict[str, dict[str, Any]]:
        """Fetch all parameters from the device.

        Returns:
            Dictionary of parameters keyed by parameter ID (as string).
            Each parameter contains: value, name, info, minv, maxv, etc.

        """
        url = f"{self._base_url}{API_ENDPOINT_ALL_PARAMS}"

        try:
            async with self._session.get(url, auth=self._auth, timeout=10) as response:
                if response.status == 401:
                    raise EconetAuthError("Invalid authentication credentials")
                if response.status != 200:
                    raise EconetApiError(f"API returned status {response.status}")

                data = await response.json()

        except aiohttp.ClientError as err:
            raise EconetConnectionError(f"Connection error: {err}") from err

        # Handle both response formats:
        # 1. Direct params object: {"0": {...}, "1": {...}, ...}
        # 2. Wrapped in allParams: {"allParams": "{\"0\": {...}, ...}"}
        if "allParams" in data:
            # Wrapped format - allParams is a JSON string
            all_params_str = data.get("allParams", "{}")
            try:
                params = json.loads(all_params_str)
            except json.JSONDecodeError as err:
                raise EconetApiError(f"Failed to parse allParams JSON: {err}") from err
        else:
            # Direct format - data is already the params dict
            params = data

        _LOGGER.debug("Fetched %d parameters from device", len(params))
        return params

    async def async_set_param(self, param_id: int, value: Any) -> bool:
        """Set a parameter value on the device.

        Args:
            param_id: The parameter ID to set.
            value: The new value.

        Returns:
            True if successful.

        """
        url = f"{self._base_url}{API_ENDPOINT_NEW_PARAM}"
        params = {
            "newParamIndex": param_id,
            "newParamValue": value,
        }

        try:
            async with self._session.get(url, auth=self._auth, params=params, timeout=10) as response:
                if response.status == 401:
                    raise EconetAuthError("Invalid authentication credentials")
                if response.status != 200:
                    raise EconetApiError(f"API returned status {response.status}")

                _LOGGER.debug("Set param %d to %s", param_id, value)
                return True

        except aiohttp.ClientError as err:
            raise EconetConnectionError(f"Connection error: {err}") from err

    async def async_test_connection(self) -> dict[str, Any]:
        """Test the connection and return device info.

        Returns:
            Dictionary with basic device info (UID, name, etc.)

        """
        params = await self.async_fetch_all_params()

        # Extract device info from params
        uid = params.get("10", {}).get("value", "unknown")
        name = params.get("374", {}).get("value", "ecoMAX")

        return {
            "uid": uid,
            "name": name,
            "param_count": len(params),
        }
