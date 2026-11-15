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
            "account_password_present",
            "account_access_keys_present",
            "mfa_devices",
            "mfa_devices_in_use",
            "users",
            "roles",
        ],
    ) == {(TEST_ACCOUNT_ID, 1, 1, 0, 3, 2, 5, 10)}


@patch("cartography.intel.aws.iam.get_account_summary")
def test_sync_account_summary_no_root_credentials(
    mock_get_account_summary, neo4j_session
):
    # Arrange: member account whose root credentials were removed via
    # Organizations centralized root access (no password, no access keys, no MFA).
    neo4j_session.run("MERGE (a:AWSAccount {id: $Account})", Account=TEST_ACCOUNT_ID)
    summary = dict(tests.data.aws.iam.account_summary.GET_ACCOUNT_SUMMARY_RESPONSE)
    summary.update(
        {
            "AccountMFAEnabled": 0,
            "AccountPasswordPresent": 0,
            "AccountAccessKeysPresent": 0,
        }
    )
    mock_get_account_summary.return_value = summary

    # Act
    cartography.intel.aws.iam.sync_account_summary(
        neo4j_session,
        "dummy_session",
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSAccount",
        [
            "id",
            "account_mfa_enabled",
            "account_password_present",
            "account_access_keys_present",
        ],
    ) == {(TEST_ACCOUNT_ID, 0, 0, 0)}


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
