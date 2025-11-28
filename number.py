"""Number platform for ecoNET Next integration."""

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONTROLLER_NUMBERS, DOMAIN, EconetNumberEntityDescription
from .coordinator import EconetNextCoordinator
from .entity import EconetNextEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ecoNET Next number entities from a config entry."""
    coordinator: EconetNextCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[EconetNextNumber] = []

    # Add controller number entities
    for description in CONTROLLER_NUMBERS:
        # Only add if parameter exists in data
        if coordinator.get_param(description.param_id) is not None:
            entities.append(EconetNextNumber(coordinator, description))
        else:
            _LOGGER.debug(
                "Skipping number %s - parameter %s not found",
                description.key,
                description.param_id,
            )

    async_add_entities(entities)


class EconetNextNumber(EconetNextEntity, NumberEntity):
    """Representation of an ecoNET Next number entity."""

    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: EconetNextCoordinator,
        description: EconetNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        # Determine device_id based on device_type
        device_id = None
        if description.device_type != "controller":
            device_id = description.device_type

        super().__init__(coordinator, description.param_id, device_id)

        self._description = description
        self._attr_translation_key = description.key

        # Apply description attributes
        if description.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        if description.entity_category:
            self._attr_entity_category = description.entity_category
        if description.icon:
            self._attr_icon = description.icon

        self._attr_native_step = description.native_step

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        value = self._get_param_value()
        if value is None:
            return None
        return float(value)

    @property
    def native_min_value(self) -> float:
        """Return the minimum value.

        If min_value_param_id is set, use that param's current value as min.
        Otherwise use the static native_min_value.
        """
        if self._description.min_value_param_id:
            dynamic_min = self.coordinator.get_param_value(self._description.min_value_param_id)
            if dynamic_min is not None:
                return float(dynamic_min)

        return self._description.native_min_value or 0

    @property
    def native_max_value(self) -> float:
        """Return the maximum value.

        If max_value_param_id is set, use that param's current value as max.
        Otherwise use the static native_max_value.
        """
        if self._description.max_value_param_id:
            dynamic_max = self.coordinator.get_param_value(self._description.max_value_param_id)
            if dynamic_max is not None:
                return float(dynamic_max)

        return self._description.native_max_value or 100

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        param_id = int(self._description.param_id)

        _LOGGER.debug(
            "Setting %s (param %d) to %s",
            self._description.key,
            param_id,
            value,
        )

        await self.coordinator.api.async_set_param(param_id, int(value))

        # Request a refresh to get the updated value
        await self.coordinator.async_request_refresh()
