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
        # Limits are read from allParams, these are just fallbacks
        assert summer_on.native_min_value == 22
        assert summer_on.native_max_value == 30

    def test_summer_mode_off_config(self) -> None:
        """Test summer mode off number has correct configuration."""
        summer_off = next(n for n in CONTROLLER_NUMBERS if n.key == "summer_mode_off")

        assert summer_off.param_id == "703"
        assert summer_off.native_unit_of_measurement == UnitOfTemperature.CELSIUS
        # Limits are read from allParams, these are just fallbacks
        assert summer_off.native_min_value == 0
        assert summer_off.native_max_value == 24


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

    def test_number_static_min_max_from_allparams(self, coordinator: EconetNextCoordinator) -> None:
        """Test number uses static minv/maxv from allParams."""
        # Param 703 has static minv=0, maxv=24 in allParams (no dynamic pointers)
        description = EconetNumberEntityDescription(
            key="summer_mode_off",
            param_id="703",
            native_min_value=999,  # Should be overridden by allParams
            native_max_value=999,  # Should be overridden by allParams
        )

        number = EconetNextNumber(coordinator, description)

        # Should read from allParams, not description
        assert number.native_min_value == 0.0  # From allParams minv
        assert number.native_max_value == 24.0  # From allParams maxvDP → param 702 value

    def test_number_dynamic_min_from_allparams(self, coordinator: EconetNextCoordinator) -> None:
        """Test number uses dynamic min from minvDP in allParams."""
        # Param 702 has minvDP=703 in allParams, which means min comes from param 703's value
        description = EconetNumberEntityDescription(
            key="summer_mode_on",
            param_id="702",
            native_min_value=999,  # Fallback (should not be used)
            native_max_value=999,
        )

        number = EconetNextNumber(coordinator, description)

        # From fixture: param 702 has minvDP=703, param 703 value=22
        assert number.native_min_value == 22.0

    def test_number_dynamic_max_from_allparams(self, coordinator: EconetNextCoordinator) -> None:
        """Test number uses dynamic max from maxvDP in allParams."""
        # Param 703 has maxvDP=702 in allParams, which means max comes from param 702's value
        description = EconetNumberEntityDescription(
            key="summer_mode_off",
            param_id="703",
            native_min_value=999,
            native_max_value=999,  # Fallback (should not be used)
        )

        number = EconetNextNumber(coordinator, description)

        # From fixture: param 703 has maxvDP=702, param 702 value=24
        assert number.native_max_value == 24.0

    def test_number_fallback_when_no_allparams(self, coordinator: EconetNextCoordinator) -> None:
        """Test number falls back to description limits when param not in allParams."""
        description = EconetNumberEntityDescription(
            key="test_number",
            param_id="99999",  # Non-existent param
            native_min_value=15,
            native_max_value=30,
        )

        number = EconetNextNumber(coordinator, description)

        # Should use fallback values from description
        assert number.native_min_value == 15
        assert number.native_max_value == 30

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

        # Coordinator converts string param_id to int before calling API
        coordinator.api.async_set_param.assert_called_once_with(702, 25)
        # Optimistic update should set the local value
        assert coordinator.data["702"]["value"] == 25
