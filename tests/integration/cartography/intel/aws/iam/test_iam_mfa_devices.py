from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j

import cartography.intel.aws.iam
from tests.data.aws.iam.mfa_devices import LIST_MFA_DEVICES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.iam,
    "get_mfa_devices",
    return_value=LIST_MFA_DEVICES,
)
def test_sync_mfa_devices(mock_get_mfa_devices, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MERGE (u1:AWSUser{name: 'user-0', arn: 'arn:aws:iam::000000000000:user/user-0'})
        MERGE (u2:AWSUser{name: 'user-1', arn: 'arn:aws:iam::000000000000:user/user-1'})
        """,
    )

    # Act
    cartography.intel.aws.iam.sync_user_mfa_devices(
        boto3_session,
        {
            "Users": [
                {"UserName": "user-0", "Arn": "arn:aws:iam::000000000000:user/user-0"},
                {"UserName": "user-1", "Arn": "arn:aws:iam::000000000000:user/user-1"},
            ]
        },
        neo4j_session,
        TEST_UPDATE_TAG,
        TEST_ACCOUNT_ID,
    )

    # Assert: Check that MFA device nodes were created with correct properties
    assert check_nodes(
        neo4j_session,
        "AWSMfaDevice",
        ["serialnumber", "username", "user_arn", "enabledate_dt"],
    ) == {
        (
            "arn:aws:iam::000000000000:mfa/user-0",
            "user-0",
            "arn:aws:iam::000000000000:user/user-0",
            neo4j.time.DateTime(2024, 1, 15, 10, 30, 0, 0),
        ),
        (
            "arn:aws:iam::000000000000:mfa/user-0-backup",
            "user-0",
            "arn:aws:iam::000000000000:user/user-0",
            neo4j.time.DateTime(2024, 2, 20, 14, 45, 0, 0),
        ),
        (
            "arn:aws:iam::000000000000:mfa/user-1",
            "user-1",
            "arn:aws:iam::000000000000:user/user-1",
            neo4j.time.DateTime(2023, 12, 1, 9, 0, 0, 0),
        ),
    }

    # Assert: Check that `MfaDevice` extra label exists
    result = neo4j_session.run(
        """
        MATCH (m:MfaDevice)
        WHERE m.serialnumber = 'arn:aws:iam::000000000000:mfa/user-0'
        RETURN m.serialnumber as serial
        """
    )
    assert result.single()["serial"] == "arn:aws:iam::000000000000:mfa/user-0"

    # Assert: Check relationships between MFA devices and users
    assert check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "AWSMfaDevice",
        "serialnumber",
        "MFA_DEVICE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:iam::000000000000:user/user-0",
            "arn:aws:iam::000000000000:mfa/user-0",
        ),
        (
            "arn:aws:iam::000000000000:user/user-0",
            "arn:aws:iam::000000000000:mfa/user-0-backup",
        ),
        (
            "arn:aws:iam::000000000000:user/user-1",
            "arn:aws:iam::000000000000:mfa/user-1",
        ),
    }

    # Assert: Check relationships between AWS account and MFA devices
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSMfaDevice",
        "serialnumber",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:iam::000000000000:mfa/user-0"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::000000000000:mfa/user-0-backup"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::000000000000:mfa/user-1"),
    }


@patch.object(
    cartography.intel.aws.iam,
    "get_mfa_devices",
    return_value=[],
)
def test_sync_mfa_devices_empty(mock_get_mfa_devices, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    # Start with a clean graph
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.iam.sync_user_mfa_devices(
        boto3_session,
        {"Users": []},
        neo4j_session,
        TEST_UPDATE_TAG,
        TEST_ACCOUNT_ID,
    )

    # Assert: No MFA devices should exist
    result = neo4j_session.run("MATCH (m:AWSMfaDevice) RETURN count(m) as count")
    assert result.single()["count"] == 0
