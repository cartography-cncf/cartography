from unittest.mock import MagicMock

import pytest

import cartography.intel.sweet
from cartography.config import Config


def _config(**sweet_options) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        **sweet_options,
    )


def test_tenant_id_without_credentials_fails_the_run():
    # Arrange
    config = _config(sweet_tenant_id="example-tenant")

    # Act and assert
    with pytest.raises(
        ValueError,
        match="missing sweet_api_key, sweet_api_secret",
    ):
        cartography.intel.sweet.start_sweet_ingestion(MagicMock(), config)


def test_credentials_without_tenant_id_fail_the_run():
    # Arrange
    config = _config(sweet_api_key="key", sweet_api_secret="secret")

    # Act and assert
    with pytest.raises(ValueError, match="missing sweet_tenant_id"):
        cartography.intel.sweet.start_sweet_ingestion(MagicMock(), config)


def test_invalid_api_url_fails_the_run():
    # Arrange
    config = _config(
        sweet_api_key="key",
        sweet_api_secret="secret",
        sweet_tenant_id="example-tenant",
        sweet_api_url="https://eapi.sweet.security:99999",
    )

    # Act and assert
    with pytest.raises(ValueError, match="invalid port"):
        cartography.intel.sweet.start_sweet_ingestion(MagicMock(), config)
