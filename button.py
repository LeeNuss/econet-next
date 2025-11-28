"""Button platform for ecoNET Next integration."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DHW_BUTTONS, DOMAIN, EconetButtonEntityDescription
from .coordinator import EconetNextCoordinator
from .entity import EconetNextEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ecoNET Next button entities from a config entry."""
    coordinator: EconetNextCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[EconetNextButton] = []

    # Add DHW button entities if DHW device should be created
    dhw_temp_param = coordinator.get_param("61")
    if dhw_temp_param is not None:
        dhw_temp_value = dhw_temp_param.get("value")
        if dhw_temp_value is not None and dhw_temp_value != 999.0:
            for description in DHW_BUTTONS:
                if coordinator.get_param(description.param_id) is not None:
                    entities.append(EconetNextButton(coordinator, description))
                else:
                    _LOGGER.debug(
                        "Skipping DHW button %s - parameter %s not found",
                        description.key,
                        description.param_id,
                    )

    async_add_entities(entities)


class EconetNextButton(EconetNextEntity, ButtonEntity):
    """Representation of an ecoNET Next button entity."""

    def __init__(
        self,
        coordinator: EconetNextCoordinator,
        description: EconetButtonEntityDescription,
    ) -> None:
        """Initialize the button entity."""
        # Determine device_id based on device_type
        device_id = None
        if description.device_type != "controller":
            device_id = description.device_type

        super().__init__(coordinator, description.param_id, device_id)

        self._description = description
        self._attr_translation_key = description.key

        # Apply description attributes
        if description.entity_category:
            self._attr_entity_category = description.entity_category
        if description.icon:
            self._attr_icon = description.icon

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug(
            "Pressing button %s (param %s)",
            self._description.key,
            self._description.param_id,
        )
        # Buttons typically set parameter to 1 to trigger an action
        await self.coordinator.async_set_param(self._description.param_id, 1)
