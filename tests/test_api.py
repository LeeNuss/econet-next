"""Tests for the econet_next API client."""

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from econet_next.api import (
    EconetApiError,
    EconetAuthError,
    EconetConnectionError,
    EconetNextApi,
)


class TestEconetNextApi:
    """Test the EconetNextApi class."""

    def test_init(self, mock_session: MagicMock) -> None:
        """Test API client initialization."""
        api = EconetNextApi(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="password",
            session=mock_session,
        )

        assert api.host == "192.168.1.100"
        assert api.port == 8080
        assert api._base_url == "http://192.168.1.100:8080"

    def test_init_custom_port(self, mock_session: MagicMock) -> None:
        """Test API client with custom port."""
        api = EconetNextApi(
            host="192.168.1.100",
            port=80,
            username="admin",
            password="password",
            session=mock_session,
        )

        assert api._base_url == "http://192.168.1.100:80"


class TestFetchAllParams:
    """Test the async_fetch_all_params method."""

    @pytest.mark.asyncio
    async def test_fetch_all_params_success(
        self,
        mock_session: MagicMock,
        all_params_response: dict,
        all_params_parsed: dict,
    ) -> None:
        """Test successful fetch of all parameters."""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=all_params_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_response)

        api = EconetNextApi(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="password",
            session=mock_session,
        )

        result = await api.async_fetch_all_params()

        assert isinstance(result, dict)
        assert len(result) == len(all_params_parsed)
        # Check some known parameters
        assert "10" in result  # UID
        assert "374" in result  # Nazwa (device name)
        assert result["10"]["name"] == "UID"
        assert result["374"]["name"] == "Nazwa"

    @pytest.mark.asyncio
    async def test_fetch_all_params_auth_error(self, mock_session: MagicMock) -> None:
        """Test authentication error handling."""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_response)

        api = EconetNextApi(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="wrong_password",
            session=mock_session,
        )

        with pytest.raises(EconetAuthError):
            await api.async_fetch_all_params()

    @pytest.mark.asyncio
    async def test_fetch_all_params_api_error(self, mock_session: MagicMock) -> None:
        """Test API error handling for non-200 status."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_response)

        api = EconetNextApi(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="password",
            session=mock_session,
        )

        with pytest.raises(EconetApiError, match="status 500"):
            await api.async_fetch_all_params()

    @pytest.mark.asyncio
    async def test_fetch_all_params_connection_error(self, mock_session: MagicMock) -> None:
        """Test connection error handling."""
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))

        api = EconetNextApi(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="password",
            session=mock_session,
        )

        with pytest.raises(EconetConnectionError, match="Connection error"):
            await api.async_fetch_all_params()

    @pytest.mark.asyncio
    async def test_fetch_all_params_invalid_json(self, mock_session: MagicMock) -> None:
        """Test handling of invalid JSON in allParams field."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"allParams": "not valid json {{{"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_response)

        api = EconetNextApi(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="password",
            session=mock_session,
        )

        with pytest.raises(EconetApiError, match="Failed to parse"):
            await api.async_fetch_all_params()


class TestSetParam:
    """Test the async_set_param method."""

    @pytest.mark.asyncio
    async def test_set_param_success(self, mock_session: MagicMock) -> None:
        """Test successful parameter set."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_response)

        api = EconetNextApi(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="password",
            session=mock_session,
        )

        result = await api.async_set_param(103, 45)

        assert result is True
        # Verify the correct URL was called
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert "/econet/newParam" in call_args[0][0]
        assert call_args[1]["params"]["newParamName"] == "103"
        assert call_args[1]["params"]["newParamValue"] == "45"

    @pytest.mark.asyncio
    async def test_set_param_auth_error(self, mock_session: MagicMock) -> None:
        """Test authentication error when setting parameter."""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_response)

        api = EconetNextApi(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="password",
            session=mock_session,
        )

        with pytest.raises(EconetAuthError):
            await api.async_set_param(103, 45)


class TestTestConnection:
    """Test the async_test_connection method."""

    @pytest.mark.asyncio
    async def test_connection_returns_device_info(
        self,
        mock_session: MagicMock,
        all_params_response: dict,
    ) -> None:
        """Test that test_connection returns device info."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=all_params_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.get = MagicMock(return_value=mock_response)

        api = EconetNextApi(
            host="192.168.1.100",
            port=8080,
            username="admin",
            password="password",
            session=mock_session,
        )

        result = await api.async_test_connection()

        assert "uid" in result
        assert "name" in result
        assert "param_count" in result
        assert result["uid"] == "2L7SDPN6KQ38CIH2401K01U"
        assert result["name"] == "ecoMAX360i"
        assert result["param_count"] > 0
