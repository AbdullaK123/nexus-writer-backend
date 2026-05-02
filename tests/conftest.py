"""Test infrastructure for the service layer.

The architecture is now repository-based, so service tests inject mocked
repositories directly (see test files). No DB, no ORM, no schema setup.
"""
import pytest


@pytest.fixture
def silence_logger(mocker):
    """Quiet loguru in tests that assert on logging side effects elsewhere."""
    return mocker.patch("loguru.logger")
