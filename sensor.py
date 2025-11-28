"""Sensor platform for ecoNET Next integration."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONTROLLER_SENSORS, DOMAIN, EconetSensorEntityDescription
from .coordinator import EconetNextCoordinator
from .entity import EconetNextEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ecoNET Next sensors from a config entry."""
    coordinator: EconetNextCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[EconetNextSensor] = []

    # Add controller sensors
    for description in CONTROLLER_SENSORS:
        # Only add if parameter exists in data
        if coordinator.get_param(description.param_id) is not None:
            entities.append(EconetNextSensor(coordinator, description))
        else:
            _LOGGER.debug(
                "Skipping sensor %s - parameter %s not found",
                description.key,
                description.param_id,
            )

    async_add_entities(entities)


class EconetNextSensor(EconetNextEntity, SensorEntity):
    """Representation of an ecoNET Next sensor."""

    def __init__(
        self,
        coordinator: EconetNextCoordinator,
        description: EconetSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        # Determine device_id based on device_type
        device_id = None
        if description.device_type != "controller":
            device_id = description.device_type

        super().__init__(coordinator, description.param_id, device_id)

        self._description = description
        self._attr_translation_key = description.key

        # Apply description attributes
        if description.device_class:
            self._attr_device_class = description.device_class
        if description.state_class:
            self._attr_state_class = description.state_class
        if description.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        if description.entity_category:
            self._attr_entity_category = description.entity_category
        if description.icon:
            self._attr_icon = description.icon
        if description.options:
            self._attr_options = description.options

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self._get_param_value()

        if value is None:
            return None

        # Apply value mapping for enum sensors
        if self._description.value_map is not None:
            return self._description.value_map.get(int(value))

        # Apply precision if specified
        if self._description.precision is not None and isinstance(value, (int, float)):
            return round(value, self._description.precision)

        return value

    def _is_value_valid(self) -> bool:
        """Check if the parameter value is valid."""
        value = self._get_param_value()
        if value is None:
            return False

        # Temperature sensors: 999.0 means sensor disconnected
        if self._description.device_class == "temperature":
            return value != 999.0

        return True
