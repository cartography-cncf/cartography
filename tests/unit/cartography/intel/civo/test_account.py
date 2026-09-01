from unittest import mock

import pytest
import requests

import cartography.intel.civo.account


def test_account_sync_rejects_missing_id() -> None:
    with mock.patch.object(
        cartography.intel.civo.account, "get", return_value={"default_user_id": "u1"}
    ):
        # neo4j_session is never touched: require_non_empty raises before
        # load_accounts() is called.
        with pytest.raises(ValueError, match="missing required non-empty account id"):
            cartography.intel.civo.account.sync(
                mock.MagicMock(),
                mock.MagicMock(spec=requests.Session),
                {"BASE_URL": "https://api.civo.com", "UPDATE_TAG": 123},
            )
