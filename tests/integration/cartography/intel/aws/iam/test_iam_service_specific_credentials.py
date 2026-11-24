from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j

import cartography.intel.aws.iam
from tests.data.aws.iam.service_specific_credentials import (
    LIST_SERVICE_SPECIFIC_CREDENTIALS,
)
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.iam,
    "get_service_specific_credentials",
    return_value=LIST_SERVICE_SPECIFIC_CREDENTIALS,
)
def test_sync_service_specific_credentials(mock_get, neo4j_session):
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MERGE (:AWSUser{name: 'user-0', arn: 'arn:aws:iam::000000000000:user/user-0'})
        MERGE (:AWSUser{name: 'user-1', arn: 'arn:aws:iam::000000000000:user/user-1'})
        """,
    )

    # Act
    cartography.intel.aws.iam.sync_user_service_specific_credentials(
        MagicMock(),
        {"Users": []},
        neo4j_session,
        TEST_UPDATE_TAG,
        TEST_ACCOUNT_ID,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSServiceSpecificCredential",
        ["id", "servicename", "serviceusername", "status", "createdate"],
    ) == {
        (
            "ACCA00000000000000001",
            "bedrock.amazonaws.com",
            None,
            "Active",
            neo4j.time.DateTime(2025, 7, 1, 12, 0, 0, 0),
        ),
        (
            "ACCA00000000000000002",
            "codecommit.amazonaws.com",
            "user-1-at-000000000000",
            "Inactive",
            neo4j.time.DateTime(2024, 3, 5, 8, 0, 0, 0),
        ),
    }
    assert check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "AWSServiceSpecificCredential",
        "id",
        "SERVICE_SPECIFIC_CREDENTIAL",
        rel_direction_right=True,
    ) == {
        ("arn:aws:iam::000000000000:user/user-0", "ACCA00000000000000001"),
        ("arn:aws:iam::000000000000:user/user-1", "ACCA00000000000000002"),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSServiceSpecificCredential",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "ACCA00000000000000001"),
        (TEST_ACCOUNT_ID, "ACCA00000000000000002"),
    }

    # Act: a later sync no longer returns the credentials
    cartography.intel.aws.iam.cleanup_iam(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSServiceSpecificCredential", ["id"]) == set()
