"""Number platform for ecoNET Next integration."""

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONTROLLER_NUMBERS,
    DHW_NUMBERS,
    DOMAIN,
    EconetNumberEntityDescription,
)
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

    # Add DHW number entities if DHW device should be created
    dhw_temp_param = coordinator.get_param("61")
    if dhw_temp_param is not None:
        dhw_temp_value = dhw_temp_param.get("value")
        if dhw_temp_value is not None and dhw_temp_value != 999.0:
            for description in DHW_NUMBERS:
                if coordinator.get_param(description.param_id) is not None:
                    entities.append(EconetNextNumber(coordinator, description))
                else:
                    _LOGGER.debug(
                        "Skipping DHW number %s - parameter %s not found",
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

        Priority:
        1. Dynamic min from minvDP parameter (if specified in allParams)
        2. Static minv from allParams
        3. Fallback from description
        """
        param = self.coordinator.get_param(self._description.param_id)
        if param:
            # Check for dynamic min (minvDP points to another parameter)
            minv_dp = param.get("minvDP")
            if minv_dp is not None:
                dynamic_min = self.coordinator.get_param_value(minv_dp)
                if dynamic_min is not None:
                    return float(dynamic_min)

            # Check for static min in the parameter data
            minv = param.get("minv")
            if minv is not None:
                return float(minv)

        # Fallback to description value
        return self._description.native_min_value or 0

    @property
    def native_max_value(self) -> float:
        """Return the maximum value.

        Priority:
        1. Dynamic max from maxvDP parameter (if specified in allParams)
        2. Static maxv from allParams
        3. Fallback from description
        """
        param = self.coordinator.get_param(self._description.param_id)
        if param:
            # Check for dynamic max (maxvDP points to another parameter)
            maxv_dp = param.get("maxvDP")
            if maxv_dp is not None:
                dynamic_max = self.coordinator.get_param_value(maxv_dp)
                if dynamic_max is not None:
                    return float(dynamic_max)

            # Check for static max in the parameter data
            maxv = param.get("maxv")
            if maxv is not None:
                return float(maxv)

        # Fallback to description value
        return self._description.native_max_value or 100

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        # Skip processing if the value is unchanged
        if value == self.native_value:
            return

        # Validate against min/max bounds
        min_value = self.native_min_value
        max_value = self.native_max_value

        if value > max_value:
            _LOGGER.warning(
                "Requested value '%s' for %s exceeds maximum allowed value '%s'",
                value,
                self._description.key,
                max_value,
            )
            # Don't return - HA might allow slightly over max due to rounding

        if value < min_value:
            _LOGGER.warning(
                "Requested value '%s' for %s is below minimum allowed value '%s'",
                value,
                self._description.key,
                min_value,
            )
            return

        # Convert to int if the value has no fractional part
        # This ensures parameters that only accept integers receive integers,
        # while fractional values (like 0.3 for heat curves) stay as floats
        api_value = int(value) if value == int(value) else value

        _LOGGER.debug(
            "Setting %s (param %s) to %s",
            self._description.key,
            self._description.param_id,
            api_value,
        )

        # Call coordinator to set value and handle optimistic update
        result = await self.coordinator.async_set_param(self._description.param_id, api_value)

        if not result:
            _LOGGER.warning(
                "Failed to set %s (param %s) to %s",
                self._description.key,
                self._description.param_id,
                api_value,
            )
