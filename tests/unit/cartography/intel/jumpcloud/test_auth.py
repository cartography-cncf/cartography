import pytest

from cartography.intel.jumpcloud import auth


def test_build_headers_with_api_key() -> None:
    headers = auth.build_headers(api_key="test-api-key")
    assert headers["x-api-key"] == "test-api-key"
    assert headers["Content-Type"] == "application/json"


def test_build_headers_requires_api_key() -> None:
    with pytest.raises(ValueError):
        auth.build_headers()
