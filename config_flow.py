"""Config flow for ecoNET Next integration."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import EconetAuthError, EconetConnectionError, EconetNextApi
from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class EconetNextConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ecoNET Next."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await self._async_validate_input(user_input)
            except EconetConnectionError:
                errors["base"] = "cannot_connect"
            except EconetAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set unique ID based on device UID
                await self.async_set_unique_id(info["uid"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["name"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _async_validate_input(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate the user input and return device info."""
        session = async_get_clientsession(self.hass)
        api = EconetNextApi(
            host=data[CONF_HOST],
            port=data[CONF_PORT],
            username=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
            session=session,
        )

        return await api.async_test_connection()
