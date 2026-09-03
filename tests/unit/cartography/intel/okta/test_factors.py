from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.okta.factors
from cartography.intel.okta.common import OktaApiError


@patch.object(cartography.intel.okta.factors, "_cleanup_okta_user_factors")
@patch.object(cartography.intel.okta.factors, "_load_okta_user_factors")
@patch.object(
    cartography.intel.okta.factors,
    "_get_okta_user_factors",
    new_callable=AsyncMock,
)
def test_sync_skips_user_deleted_during_factor_fetch(
    mock_get_factors: AsyncMock,
    mock_load: MagicMock,
    mock_cleanup: MagicMock,
) -> None:
    # Arrange
    mock_get_factors.side_effect = [
        OktaApiError("list_factors", SimpleNamespace(error_code="E0000007")),
        [],
    ]

    # Act
    cartography.intel.okta.factors.sync_okta_user_factors(
        MagicMock(),
        MagicMock(),
        {"UPDATE_TAG": 1, "OKTA_ORG_ID": "org"},
        ["gone", "live"],
    )

    # Assert
    assert mock_get_factors.await_count == 2
    mock_load.assert_called_once()
    mock_cleanup.assert_called_once()


@patch.object(
    cartography.intel.okta.factors,
    "_get_okta_user_factors",
    new_callable=AsyncMock,
)
def test_sync_reraises_other_factor_api_errors(mock_get_factors: AsyncMock) -> None:
    # Arrange
    mock_get_factors.side_effect = OktaApiError(
        "list_factors", SimpleNamespace(error_code="E0000011")
    )

    # Act and assert
    with pytest.raises(OktaApiError):
        cartography.intel.okta.factors.sync_okta_user_factors(
            MagicMock(), MagicMock(), {"UPDATE_TAG": 1, "OKTA_ORG_ID": "org"}, ["user"]
        )
