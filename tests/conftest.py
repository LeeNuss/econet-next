"""Test configuration for econet_next integration tests."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from aiohttp import ClientSession

# Add grandparent directory to path so we can import custom_components.econet_next
# The path structure is: .../custom_components/econet_next/tests/conftest.py
# We need to add .../custom_components to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def fixture_path() -> Path:
    """Return the path to test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def all_params_response(fixture_path: Path) -> dict:
    """Load the allParams.json fixture as API response format."""
    with open(fixture_path / "allParams.json") as f:
        return json.load(f)


@pytest.fixture
def all_params_parsed(all_params_response: dict) -> dict:
    """Parse the allParams field from the response."""
    return json.loads(all_params_response["allParams"])


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock aiohttp ClientSession."""
    session = MagicMock(spec=ClientSession)
    return session


@pytest.fixture
def mock_response() -> MagicMock:
    """Create a mock aiohttp response."""
    response = MagicMock()
    response.status = 200
    return response
