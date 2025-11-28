"""Tests for the econet_next switch platform."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from econet_next.const import CONTROLLER_SWITCHES, EconetSwitchEntityDescription
from econet_next.coordinator import EconetNextCoordinator
from econet_next.switch import EconetNextSwitch


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


class TestControllerSwitchesDefinition:
    """Test that controller switch definitions are correct."""

    def test_all_switches_have_required_fields(self) -> None:
        """Test all switches have required key and param_id."""
        for switch in CONTROLLER_SWITCHES:
            assert switch.key, "Switch must have a key"
            assert switch.param_id, "Switch must have a param_id"

    def test_cooling_support_config(self) -> None:
        """Test cooling support switch has correct configuration."""
        cooling_support = next(s for s in CONTROLLER_SWITCHES if s.key == "cooling_support")

        assert cooling_support.param_id == "485"
        assert cooling_support.icon == "mdi:snowflake"


class TestEconetNextSwitch:
    """Test the EconetNextSwitch class."""

    def test_switch_initialization(self, coordinator: EconetNextCoordinator) -> None:
        """Test switch initialization."""
        description = EconetSwitchEntityDescription(
            key="cooling_support",
            param_id="485",
            icon="mdi:snowflake",
        )

        switch = EconetNextSwitch(coordinator, description)

        assert switch._attr_translation_key == "cooling_support"
        assert switch._attr_icon == "mdi:snowflake"

    def test_switch_is_on_true(self, coordinator: EconetNextCoordinator) -> None:
        """Test switch returns True when value is 1."""
        coordinator.data["485"] = {"id": 485, "value": 1}

        description = EconetSwitchEntityDescription(
            key="cooling_support",
            param_id="485",
        )

        switch = EconetNextSwitch(coordinator, description)
        assert switch.is_on is True

    def test_switch_is_on_false(self, coordinator: EconetNextCoordinator) -> None:
        """Test switch returns False when value is 0."""
        coordinator.data["485"] = {"id": 485, "value": 0}

        description = EconetSwitchEntityDescription(
            key="cooling_support",
            param_id="485",
        )

        switch = EconetNextSwitch(coordinator, description)
        assert switch.is_on is False

    def test_switch_is_on_none(self, coordinator: EconetNextCoordinator) -> None:
        """Test switch returns None when value is None."""
        coordinator.data["485"] = {"id": 485, "value": None}

        description = EconetSwitchEntityDescription(
            key="cooling_support",
            param_id="485",
        )

        switch = EconetNextSwitch(coordinator, description)
        assert switch.is_on is None

    def test_switch_is_on_missing_param(self, coordinator: EconetNextCoordinator) -> None:
        """Test switch returns None when param is missing."""
        # Use a param ID that doesn't exist in the fixture
        description = EconetSwitchEntityDescription(
            key="test_switch",
            param_id="99999",
        )

        switch = EconetNextSwitch(coordinator, description)
        assert switch.is_on is None

    @pytest.mark.asyncio
    async def test_turn_on(self, coordinator: EconetNextCoordinator) -> None:
        """Test turning switch on."""
        description = EconetSwitchEntityDescription(
            key="cooling_support",
            param_id="485",
        )

        switch = EconetNextSwitch(coordinator, description)
        await switch.async_turn_on()

        coordinator.api.async_set_param.assert_called_once_with(485, 1)
        coordinator.async_request_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off(self, coordinator: EconetNextCoordinator) -> None:
        """Test turning switch off."""
        description = EconetSwitchEntityDescription(
            key="cooling_support",
            param_id="485",
        )

        switch = EconetNextSwitch(coordinator, description)
        await switch.async_turn_off()

        coordinator.api.async_set_param.assert_called_once_with(485, 0)
        coordinator.async_request_refresh.assert_called_once()
