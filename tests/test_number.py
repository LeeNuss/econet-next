"""Tests for the econet_next number platform."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import UnitOfTemperature

from econet_next.const import CONTROLLER_NUMBERS, EconetNumberEntityDescription
from econet_next.coordinator import EconetNextCoordinator
from econet_next.number import EconetNextNumber


@pytest.fixture(autouse=True)
def patch_frame_helper():
    """Patch Home Assistant frame helper for all tests."""
    with patch("homeassistant.helpers.frame.report_usage"):
        yield


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create a mock Home Assistant instance."""
    hass = MagicMock()
    return hass


@pytest.fixture
def mock_api() -> MagicMock:
    """Create a mock API."""
    api = MagicMock()
    api.async_set_param = AsyncMock(return_value=True)
    return api


@pytest.fixture
def coordinator(mock_hass: MagicMock, mock_api: MagicMock, all_params_parsed: dict) -> EconetNextCoordinator:
    """Create a coordinator with data."""
    coordinator = EconetNextCoordinator(mock_hass, mock_api)
    coordinator.data = all_params_parsed
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


class TestControllerNumbersDefinition:
    """Test that controller number definitions are correct."""

    def test_all_numbers_have_required_fields(self) -> None:
        """Test all numbers have required key and param_id."""
        for number in CONTROLLER_NUMBERS:
            assert number.key, "Number must have a key"
            assert number.param_id, "Number must have a param_id"

    def test_summer_mode_on_config(self) -> None:
        """Test summer mode on number has correct configuration."""
        summer_on = next(n for n in CONTROLLER_NUMBERS if n.key == "summer_mode_on")

        assert summer_on.param_id == "702"
        assert summer_on.native_unit_of_measurement == UnitOfTemperature.CELSIUS
        assert summer_on.native_min_value == 22
        assert summer_on.native_max_value == 30
        assert summer_on.min_value_param_id == "703"  # Dynamic min from SummerOff

    def test_summer_mode_off_config(self) -> None:
        """Test summer mode off number has correct configuration."""
        summer_off = next(n for n in CONTROLLER_NUMBERS if n.key == "summer_mode_off")

        assert summer_off.param_id == "703"
        assert summer_off.native_unit_of_measurement == UnitOfTemperature.CELSIUS
        assert summer_off.native_min_value == 0
        assert summer_off.native_max_value == 24
        assert summer_off.max_value_param_id == "702"  # Dynamic max from SummerOn


class TestEconetNextNumber:
    """Test the EconetNextNumber class."""

    def test_number_initialization(self, coordinator: EconetNextCoordinator) -> None:
        """Test number initialization."""
        description = EconetNumberEntityDescription(
            key="test_number",
            param_id="702",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            native_min_value=10,
            native_max_value=30,
        )

        number = EconetNextNumber(coordinator, description)

        assert number._attr_translation_key == "test_number"
        assert number._attr_native_unit_of_measurement == UnitOfTemperature.CELSIUS

    def test_number_native_value(self, coordinator: EconetNextCoordinator) -> None:
        """Test number returns correct native value."""
        description = EconetNumberEntityDescription(
            key="summer_mode_on",
            param_id="702",
            native_min_value=22,
            native_max_value=30,
        )

        number = EconetNextNumber(coordinator, description)
        value = number.native_value

        # From fixture, param 702 (SummerOn) = 24
        assert value == 24.0

    def test_number_static_min_max(self, coordinator: EconetNextCoordinator) -> None:
        """Test number uses static min/max when no dynamic params specified."""
        description = EconetNumberEntityDescription(
            key="test_number",
            param_id="702",
            native_min_value=10,
            native_max_value=50,
        )

        number = EconetNextNumber(coordinator, description)

        assert number.native_min_value == 10
        assert number.native_max_value == 50

    def test_number_dynamic_min_value(self, coordinator: EconetNextCoordinator) -> None:
        """Test number uses dynamic min from another param's value."""
        description = EconetNumberEntityDescription(
            key="summer_mode_on",
            param_id="702",
            native_min_value=22,  # Fallback
            native_max_value=30,
            min_value_param_id="703",  # Min from SummerOff value
        )

        number = EconetNextNumber(coordinator, description)

        # From fixture, param 703 (SummerOff) = 22
        assert number.native_min_value == 22.0

    def test_number_dynamic_max_value(self, coordinator: EconetNextCoordinator) -> None:
        """Test number uses dynamic max from another param's value."""
        description = EconetNumberEntityDescription(
            key="summer_mode_off",
            param_id="703",
            native_min_value=0,
            native_max_value=24,  # Fallback
            max_value_param_id="702",  # Max from SummerOn value
        )

        number = EconetNextNumber(coordinator, description)

        # From fixture, param 702 (SummerOn) = 24
        assert number.native_max_value == 24.0

    def test_number_dynamic_min_fallback(self, coordinator: EconetNextCoordinator) -> None:
        """Test number falls back to static min when dynamic param not found."""
        description = EconetNumberEntityDescription(
            key="test_number",
            param_id="702",
            native_min_value=15,
            native_max_value=30,
            min_value_param_id="99999",  # Non-existent param
        )

        number = EconetNextNumber(coordinator, description)

        assert number.native_min_value == 15

    @pytest.mark.asyncio
    async def test_set_native_value(self, coordinator: EconetNextCoordinator) -> None:
        """Test setting a number value."""
        description = EconetNumberEntityDescription(
            key="summer_mode_on",
            param_id="702",
            native_min_value=22,
            native_max_value=30,
        )

        number = EconetNextNumber(coordinator, description)
        await number.async_set_native_value(25.0)

        coordinator.api.async_set_param.assert_called_once_with(702, 25)
        coordinator.async_request_refresh.assert_called_once()
