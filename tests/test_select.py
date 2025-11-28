"""Tests for the econet_next select platform."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from econet_next.const import (
    CONTROLLER_SELECTS,
    OPERATING_MODE_MAPPING,
    OPERATING_MODE_OPTIONS,
    OPERATING_MODE_REVERSE,
    EconetSelectEntityDescription,
)
from econet_next.coordinator import EconetNextCoordinator
from econet_next.select import EconetNextSelect


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


class TestOperatingModeConstants:
    """Test operating mode constants are correctly defined."""

    def test_operating_mode_mapping(self) -> None:
        """Test operating mode mapping has correct values."""
        assert OPERATING_MODE_MAPPING == {
            1: "summer",
            2: "winter",
            6: "auto",
        }

    def test_operating_mode_options(self) -> None:
        """Test operating mode options list."""
        assert OPERATING_MODE_OPTIONS == ["summer", "winter", "auto"]

    def test_operating_mode_reverse_mapping(self) -> None:
        """Test reverse mapping is correct."""
        assert OPERATING_MODE_REVERSE == {
            "summer": 1,
            "winter": 2,
            "auto": 6,
        }

    def test_reverse_mapping_matches_forward(self) -> None:
        """Test reverse mapping is consistent with forward mapping."""
        for raw_value, option in OPERATING_MODE_MAPPING.items():
            assert OPERATING_MODE_REVERSE[option] == raw_value


class TestControllerSelectsDefinition:
    """Test that controller select definitions are correct."""

    def test_all_selects_have_required_fields(self) -> None:
        """Test all selects have required key and param_id."""
        for select in CONTROLLER_SELECTS:
            assert select.key, "Select must have a key"
            assert select.param_id, "Select must have a param_id"
            assert select.options, "Select must have options"
            assert select.value_map, "Select must have value_map"
            assert select.reverse_map, "Select must have reverse_map"

    def test_operating_mode_config(self) -> None:
        """Test operating mode select has correct configuration."""
        operating_mode = next(s for s in CONTROLLER_SELECTS if s.key == "operating_mode")

        assert operating_mode.param_id == "162"
        assert operating_mode.options == OPERATING_MODE_OPTIONS
        assert operating_mode.value_map == OPERATING_MODE_MAPPING
        assert operating_mode.reverse_map == OPERATING_MODE_REVERSE
        assert operating_mode.icon == "mdi:sun-snowflake-variant"


class TestEconetNextSelect:
    """Test the EconetNextSelect class."""

    def test_select_initialization(self, coordinator: EconetNextCoordinator) -> None:
        """Test select initialization."""
        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            icon="mdi:sun-snowflake-variant",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)

        assert select._attr_translation_key == "operating_mode"
        assert select._attr_options == OPERATING_MODE_OPTIONS
        assert select._attr_icon == "mdi:sun-snowflake-variant"

    def test_select_current_option_winter(self, coordinator: EconetNextCoordinator) -> None:
        """Test select returns correct current option for winter mode."""
        # Set param 162 to winter (2)
        coordinator.data["162"] = {"id": 162, "value": 2}

        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)
        assert select.current_option == "winter"

    def test_select_current_option_summer(self, coordinator: EconetNextCoordinator) -> None:
        """Test select returns correct current option for summer mode."""
        coordinator.data["162"] = {"id": 162, "value": 1}

        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)
        assert select.current_option == "summer"

    def test_select_current_option_auto(self, coordinator: EconetNextCoordinator) -> None:
        """Test select returns correct current option for auto mode."""
        coordinator.data["162"] = {"id": 162, "value": 6}

        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)
        assert select.current_option == "auto"

    def test_select_current_option_unknown_value(self, coordinator: EconetNextCoordinator) -> None:
        """Test select returns None for unknown raw value."""
        coordinator.data["162"] = {"id": 162, "value": 99}

        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)
        assert select.current_option is None

    def test_select_current_option_none_value(self, coordinator: EconetNextCoordinator) -> None:
        """Test select returns None when param value is None."""
        coordinator.data["162"] = {"id": 162, "value": None}

        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)
        assert select.current_option is None

    @pytest.mark.asyncio
    async def test_select_option_winter(self, coordinator: EconetNextCoordinator) -> None:
        """Test setting select to winter."""
        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)
        await select.async_select_option("winter")

        coordinator.api.async_set_param.assert_called_once_with(162, 2)
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_option_summer(self, coordinator: EconetNextCoordinator) -> None:
        """Test setting select to summer."""
        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)
        await select.async_select_option("summer")

        coordinator.api.async_set_param.assert_called_once_with(162, 1)
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_option_auto(self, coordinator: EconetNextCoordinator) -> None:
        """Test setting select to auto."""
        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)
        await select.async_select_option("auto")

        coordinator.api.async_set_param.assert_called_once_with(162, 6)
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_option_unknown(self, coordinator: EconetNextCoordinator) -> None:
        """Test setting select to unknown option does nothing."""
        description = EconetSelectEntityDescription(
            key="operating_mode",
            param_id="162",
            options=OPERATING_MODE_OPTIONS,
            value_map=OPERATING_MODE_MAPPING,
            reverse_map=OPERATING_MODE_REVERSE,
        )

        select = EconetNextSelect(coordinator, description)
        await select.async_select_option("unknown_option")

        coordinator.api.async_set_param.assert_not_called()
        coordinator.async_request_refresh.assert_not_called()
