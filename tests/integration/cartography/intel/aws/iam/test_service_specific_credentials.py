from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.iam
from tests.data.aws.iam.service_specific_credentials import (
    GET_USER_SERVICE_SPECIFIC_CREDENTIALS_DATA_MAPPED,
)
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "1234"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.iam,
    "get_user_service_specific_credentials_data",
    return_value=GET_USER_SERVICE_SPECIFIC_CREDENTIALS_DATA_MAPPED,
)
def test_sync_user_service_specific_credentials(
    mock_get_user_service_specific_credentials_data,
    neo4j_session,
):
    """Test that service-specific credentials sync correctly and create proper nodes and relationships"""
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Create test users first (they need to exist for the sync to work)
    users_data = [
        {
            "name": "user1",
            "arn": "arn:aws:iam::1234:user/user1",
        },
        {
            "name": "user2",
            "arn": "arn:aws:iam::1234:user/user2",
        },
        {
            "name": "user3",
            "arn": "arn:aws:iam::1234:user/user3",
        },
    ]
    # Load users into the graph
    user_transformed_data = [
        {
            "arn": "arn:aws:iam::1234:user/user1",
            "userid": "AIDA00000000000000001",
            "name": "user1",
            "path": "/",
            "createdate": "2023-01-01 00:00:00",
            "passwordlastused": "",
        },
        {
            "arn": "arn:aws:iam::1234:user/user2",
            "userid": "AIDA00000000000000002",
            "name": "user2",
            "path": "/",
            "createdate": "2023-01-01 00:00:00",
            "passwordlastused": "",
        },
        {
            "arn": "arn:aws:iam::1234:user/user3",
            "userid": "AIDA00000000000000003",
            "name": "user3",
            "path": "/",
            "createdate": "2023-01-01 00:00:00",
            "passwordlastused": "",
        },
    ]
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        user_transformed_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act - Call the sync function
    cartography.intel.aws.iam.sync_user_service_specific_credentials(
        neo4j_session,
        boto3_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Verify nodes were created
    expected_nodes = {
        ("AIDAIOSFODNN7EXAMPLE", "AIDAIOSFODNN7EXAMPLE"),
        ("AIDAI44QH8DHBEXAMPLE", "AIDAI44QH8DHBEXAMPLE"),
        ("AIDAJQ5CMEXAMPLE", "AIDAJQ5CMEXAMPLE"),
    }
    assert (
        check_nodes(
            neo4j_session,
            "ServiceSpecificCredential",
            ["service_specific_credential_id", "id"],
        )
        == expected_nodes
    )

    # Assert - Verify relationships to AWSUser were created
    expected_user_rels = {
        ("AIDAIOSFODNN7EXAMPLE", "arn:aws:iam::1234:user/user1"),
        ("AIDAI44QH8DHBEXAMPLE", "arn:aws:iam::1234:user/user1"),
        ("AIDAJQ5CMEXAMPLE", "arn:aws:iam::1234:user/user2"),
    }
    assert (
        check_rels(
            neo4j_session,
            "ServiceSpecificCredential",
            "service_specific_credential_id",
            "AWSUser",
            "arn",
            "SERVICE_SPECIFIC_CREDENTIAL",
            rel_direction_right=False,
        )
        == expected_user_rels
    )

    # Assert - Verify relationships to AWSAccount were created
    expected_account_rels = {
        ("AIDAIOSFODNN7EXAMPLE", TEST_ACCOUNT_ID),
        ("AIDAI44QH8DHBEXAMPLE", TEST_ACCOUNT_ID),
        ("AIDAJQ5CMEXAMPLE", TEST_ACCOUNT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ServiceSpecificCredential",
            "service_specific_credential_id",
            "AWSAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_account_rels
    )