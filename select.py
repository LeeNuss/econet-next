"""Select platform for ecoNET Next integration."""

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONTROLLER_SELECTS, DOMAIN, EconetSelectEntityDescription
from .coordinator import EconetNextCoordinator
from .entity import EconetNextEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ecoNET Next select entities from a config entry."""
    coordinator: EconetNextCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[EconetNextSelect] = []

    # Add controller select entities
    for description in CONTROLLER_SELECTS:
        # Only add if parameter exists in data
        if coordinator.get_param(description.param_id) is not None:
            entities.append(EconetNextSelect(coordinator, description))
        else:
            _LOGGER.debug(
                "Skipping select %s - parameter %s not found",
                description.key,
                description.param_id,
            )

    async_add_entities(entities)


class EconetNextSelect(EconetNextEntity, SelectEntity):
    """Representation of an ecoNET Next select entity."""

    def __init__(
        self,
        coordinator: EconetNextCoordinator,
        description: EconetSelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        # Determine device_id based on device_type
        device_id = None
        if description.device_type != "controller":
            device_id = description.device_type

        super().__init__(coordinator, description.param_id, device_id)

        self._description = description
        self._attr_translation_key = description.key
        self._attr_options = description.options

        # Apply description attributes
        if description.entity_category:
            self._attr_entity_category = description.entity_category
        if description.icon:
            self._attr_icon = description.icon

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        value = self._get_param_value()
        if value is None:
            return None

        # Map the raw value to an option string
        return self._description.value_map.get(int(value))

    async def async_select_option(self, option: str) -> None:
        """Set the selected option."""
        # Map the option string to raw value
        raw_value = self._description.reverse_map.get(option)
        if raw_value is None:
            _LOGGER.error("Unknown option %s for %s", option, self._description.key)
            return

        param_id = int(self._description.param_id)

        _LOGGER.debug(
            "Setting %s (param %d) to %s (raw: %d)",
            self._description.key,
            param_id,
            option,
            raw_value,
        )

        await self.coordinator.api.async_set_param(param_id, raw_value)

        # Request a refresh to get the updated value
        await self.coordinator.async_request_refresh()
