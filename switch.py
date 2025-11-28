"""Switch platform for ecoNET Next integration."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONTROLLER_SWITCHES,
    DHW_SWITCHES,
    DOMAIN,
    EconetSwitchEntityDescription,
)
from .coordinator import EconetNextCoordinator
from .entity import EconetNextEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ecoNET Next switch entities from a config entry."""
    coordinator: EconetNextCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[EconetNextSwitch] = []

    # Add controller switch entities
    for description in CONTROLLER_SWITCHES:
        # Only add if parameter exists in data
        if coordinator.get_param(description.param_id) is not None:
            entities.append(EconetNextSwitch(coordinator, description))
        else:
            _LOGGER.debug(
                "Skipping switch %s - parameter %s not found",
                description.key,
                description.param_id,
            )

    # Add DHW switch entities if DHW device should be created
    dhw_temp_param = coordinator.get_param("61")
    if dhw_temp_param is not None:
        dhw_temp_value = dhw_temp_param.get("value")
        if dhw_temp_value is not None and dhw_temp_value != 999.0:
            for description in DHW_SWITCHES:
                if coordinator.get_param(description.param_id) is not None:
                    entities.append(EconetNextSwitch(coordinator, description))
                else:
                    _LOGGER.debug(
                        "Skipping DHW switch %s - parameter %s not found",
                        description.key,
                        description.param_id,
                    )

    async_add_entities(entities)


class EconetNextSwitch(EconetNextEntity, SwitchEntity):
    """Representation of an ecoNET Next switch entity."""

    def __init__(
        self,
        coordinator: EconetNextCoordinator,
        description: EconetSwitchEntityDescription,
    ) -> None:
        """Initialize the switch entity."""
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

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        value = self._get_param_value()
        if value is None:
            return None
        # API uses 1 for on, 0 for off
        return bool(int(value))

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        _LOGGER.debug(
            "Turning on %s (param %s)",
            self._description.key,
            self._description.param_id,
        )
        await self.coordinator.async_set_param(self._description.param_id, 1)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        _LOGGER.debug(
            "Turning off %s (param %s)",
            self._description.key,
            self._description.param_id,
        )
        await self.coordinator.async_set_param(self._description.param_id, 0)
