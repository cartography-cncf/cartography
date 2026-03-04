from unittest.mock import patch

import pytest

import cartography.intel.aws.iam
import tests.data.aws.iam.account_summary
from tests.integration.util import check_nodes

TEST_ACCOUNT_ID = "123456789012"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.aws.iam.get_account_summary")
def test_sync_account_summary(mock_get_account_summary, neo4j_session):
    neo4j_session.run("MERGE (a:AWSAccount {id: $Account})", Account=TEST_ACCOUNT_ID)
    mock_get_account_summary.return_value = (
        tests.data.aws.iam.account_summary.GET_ACCOUNT_SUMMARY_RESPONSE
    )

    cartography.intel.aws.iam.sync_account_summary(
        neo4j_session,
        "dummy_session",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    assert check_nodes(
        neo4j_session,
        "AWSAccount",
        [
            "id",
            "account_mfa_enabled",
            "mfa_devices",
            "mfa_devices_in_use",
            "users",
            "roles",
        ],
    ) == {(TEST_ACCOUNT_ID, 1, 3, 2, 5, 10)}


@patch("cartography.intel.aws.iam.get_account_summary")
def test_sync_account_summary_missing_summary_map(
    mock_get_account_summary,
    neo4j_session,
):
    mock_get_account_summary.side_effect = KeyError("SummaryMap")

    with pytest.raises(KeyError, match="SummaryMap"):
        cartography.intel.aws.iam.sync_account_summary(
            neo4j_session,
            "dummy_session",
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
        )
