from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.iam
from cartography.intel.aws.iam import sync
from tests.data.aws.iam import GET_GROUP_MEMBERSHIPS_DATA
from tests.data.aws.iam import LIST_GROUPS_SAMPLE
from tests.data.aws.iam.access_keys import GET_USER_ACCESS_KEYS_DATA
from tests.data.aws.iam.group_policies import GET_GROUP_INLINE_POLS_SAMPLE
from tests.data.aws.iam.group_policies import GET_GROUP_MANAGED_POLICY_DATA
from tests.data.aws.iam.role_inline_policies import GET_ROLE_INLINE_POLS_SAMPLE
from tests.data.aws.iam.role_policies import (
    ANOTHER_GET_ROLE_LIST_DATASET as GET_ROLE_LIST_DATA,
)
from tests.data.aws.iam.role_policies import GET_ROLE_MANAGED_POLICY_DATA
from tests.data.aws.iam.service_specific_credentials import (
    GET_USER_SERVICE_SPECIFIC_CREDENTIALS_DATA,
)
from tests.data.aws.iam.user_inline_policies import GET_USER_INLINE_POLS_SAMPLE
from tests.data.aws.iam.user_policies import GET_USER_LIST_DATA
from tests.data.aws.iam.user_policies import GET_USER_MANAGED_POLS_SAMPLE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "1234"
TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 123456790


@patch.object(
    cartography.intel.aws.iam,
    "get_server_certificates",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.iam,
    "get_saml_providers",
    return_value={"SAMLProviderList": []},
)
@patch.object(
    cartography.intel.aws.iam,
    "sync_service_last_accessed_details",
)
@patch.object(
    cartography.intel.aws.iam,
    "get_group_memberships",
    return_value=GET_GROUP_MEMBERSHIPS_DATA,
)
@patch.object(
    cartography.intel.aws.iam,
    "get_role_managed_policy_data",
    return_value=GET_ROLE_MANAGED_POLICY_DATA,
)
@patch.object(
    cartography.intel.aws.iam,
    "get_role_policy_data",
    return_value=GET_ROLE_INLINE_POLS_SAMPLE,
)
@patch.object(
    cartography.intel.aws.iam, "get_role_list_data", return_value=GET_ROLE_LIST_DATA
)
@patch.object(
    cartography.intel.aws.iam,
    "get_group_managed_policy_data",
    return_value=GET_GROUP_MANAGED_POLICY_DATA,
)
@patch.object(
    cartography.intel.aws.iam,
    "get_group_policy_data",
    return_value=GET_GROUP_INLINE_POLS_SAMPLE,
)
@patch.object(
    cartography.intel.aws.iam, "get_group_list_data", return_value=LIST_GROUPS_SAMPLE
)
@patch.object(
    cartography.intel.aws.iam,
    "get_user_managed_policy_data",
    return_value=GET_USER_MANAGED_POLS_SAMPLE,
)
@patch.object(
    cartography.intel.aws.iam,
    "get_user_policy_data",
    return_value=GET_USER_INLINE_POLS_SAMPLE,
)
@patch.object(
    cartography.intel.aws.iam, "get_user_list_data", return_value=GET_USER_LIST_DATA
)
@patch.object(
    cartography.intel.aws.iam,
    "get_user_access_keys_data",
    return_value=GET_USER_ACCESS_KEYS_DATA,
)
@patch.object(
    cartography.intel.aws.iam,
    "get_user_service_specific_credentials_data",
    return_value=GET_USER_SERVICE_SPECIFIC_CREDENTIALS_DATA,
)
def test_sync_iam(
    mock_get_user_service_specific_credentials_data,
    mock_get_user_access_keys,
    mock_get_user_list_data,
    mock_get_user_policy_data,
    mock_get_user_managed_policy_data,
    mock_get_group_list_data,
    mock_get_group_policy_data,
    mock_get_group_managed_policy_data,
    mock_get_role_list_data,
    mock_get_role_policy_data,
    mock_get_role_managed_policy_data,
    mock_get_group_memberships,
    mock_sync_service_last_accessed_details,
    mock_get_saml_providers,
    mock_get_server_certificates,
    neo4j_session,
):
    """Test IAM sync end-to-end"""
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    # Assert: AWSAccount -> AWSPrincipal
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSPrincipal",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:root"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:user/user1"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:user/user2"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:user/user3"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:role/ServiceRole"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:role/ElasticacheAutoscale"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:role/sftp-LambdaExecutionRole-1234"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:group/example-group-0"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:group/example-group-1"),
        # Additional principals from trust relationships
        ("54321", "arn:aws:iam::54321:root"),
    }, "AWSPrincipals not connected to AWSAccount"

    # AWSPrincipal -> AWSPolicy
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "arn",
        "AWSPolicy",
        "id",
        "POLICY",
        rel_direction_right=True,
    ) == {
        # User policies
        ("arn:aws:iam::1234:user/user1", "arn:aws:iam::1234:policy/user1-user-policy"),
        ("arn:aws:iam::1234:user/user1", "arn:aws:iam::aws:policy/AmazonS3FullAccess"),
        (
            "arn:aws:iam::1234:user/user1",
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess",
        ),
        (
            "arn:aws:iam::1234:user/user1",
            "arn:aws:iam::1234:user/user1/inline_policy/user1_inline_policy",
        ),
        (
            "arn:aws:iam::1234:user/user2",
            "arn:aws:iam::1234:user/user2/inline_policy/user2_admin_policy",
        ),
        ("arn:aws:iam::1234:user/user3", "arn:aws:iam::aws:policy/AdministratorAccess"),
        # Role policies
        (
            "arn:aws:iam::1234:role/ServiceRole",
            "arn:aws:iam::1234:role/ServiceRole/inline_policy/ServiceRole",
        ),
        (
            "arn:aws:iam::1234:role/ElasticacheAutoscale",
            "arn:aws:iam::1234:policy/AWSLambdaBasicExecutionRole-autoscaleElasticache",
        ),
        (
            "arn:aws:iam::1234:role/ElasticacheAutoscale",
            "arn:aws:iam::aws:policy/AWSLambdaFullAccess",
        ),
        (
            "arn:aws:iam::1234:role/ElasticacheAutoscale",
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        ),
        (
            "arn:aws:iam::1234:role/ElasticacheAutoscale",
            "arn:aws:iam::aws:policy/service-role/AWSLambdaRole",
        ),
        (
            "arn:aws:iam::1234:role/ElasticacheAutoscale",
            "arn:aws:iam::aws:policy/AmazonElastiCacheFullAccess",
        ),
        (
            "arn:aws:iam::1234:role/sftp-LambdaExecutionRole-1234",
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
        ),
        # Group policies
        (
            "arn:aws:iam::1234:group/example-group-0",
            "arn:aws:iam::1234:group/example-group-0/inline_policy/group_inline_policy",
        ),
        (
            "arn:aws:iam::1234:group/example-group-0",
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
        ),
        (
            "arn:aws:iam::1234:group/example-group-0",
            "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess",
        ),
        (
            "arn:aws:iam::1234:group/example-group-1",
            "arn:aws:iam::1234:group/example-group-1/inline_policy/admin_policy",
        ),
        (
            "arn:aws:iam::1234:group/example-group-1",
            "arn:aws:iam::aws:policy/AdministratorAccess",
        ),
    }

    # AWSUser -MEMBER_AWS_GROUP-> AWSGroup
    assert check_rels(
        neo4j_session,
        "AWSUser",
        "arn",
        "AWSGroup",
        "arn",
        "MEMBER_AWS_GROUP",
        rel_direction_right=True,
    ) == {
        ("arn:aws:iam::1234:user/user1", "arn:aws:iam::1234:group/example-group-0"),
        ("arn:aws:iam::1234:user/user2", "arn:aws:iam::1234:group/example-group-0"),
        ("arn:aws:iam::1234:user/user3", "arn:aws:iam::1234:group/example-group-1"),
    }

    # AWSPolicy -> AWSPolicyStatement
    assert check_rels(
        neo4j_session,
        "AWSPolicy",
        "id",
        "AWSPolicyStatement",
        "id",
        "STATEMENT",
        rel_direction_right=True,
    ) == {
        # User policy statements
        (
            "arn:aws:iam::1234:policy/user1-user-policy",
            "arn:aws:iam::1234:policy/user1-user-policy/statement/VisualEditor0",
        ),
        (
            "arn:aws:iam::1234:policy/user1-user-policy",
            "arn:aws:iam::1234:policy/user1-user-policy/statement/VisualEditor1",
        ),
        (
            "arn:aws:iam::aws:policy/AmazonS3FullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess/statement/1",
        ),
        (
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess",
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess/statement/1",
        ),
        (
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess",
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess/statement/2",
        ),
        (
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess",
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess/statement/3",
        ),
        (
            "arn:aws:iam::aws:policy/AdministratorAccess",
            "arn:aws:iam::aws:policy/AdministratorAccess/statement/1",
        ),
        # User inline policy statements
        (
            "arn:aws:iam::1234:user/user1/inline_policy/user1_inline_policy",
            "arn:aws:iam::1234:user/user1/inline_policy/user1_inline_policy/statement/VisualEditor0",
        ),
        (
            "arn:aws:iam::1234:user/user1/inline_policy/user1_inline_policy",
            "arn:aws:iam::1234:user/user1/inline_policy/user1_inline_policy/statement/VisualEditor1",
        ),
        (
            "arn:aws:iam::1234:user/user2/inline_policy/user2_admin_policy",
            "arn:aws:iam::1234:user/user2/inline_policy/user2_admin_policy/statement/1",
        ),
        # Role policy statements
        (
            "arn:aws:iam::1234:role/ServiceRole/inline_policy/ServiceRole",
            "arn:aws:iam::1234:role/ServiceRole/inline_policy/ServiceRole/statement/VisualEditor0",
        ),
        (
            "arn:aws:iam::1234:policy/AWSLambdaBasicExecutionRole-autoscaleElasticache",
            "arn:aws:iam::1234:policy/AWSLambdaBasicExecutionRole-autoscaleElasticache/statement/1",
        ),
        (
            "arn:aws:iam::1234:policy/AWSLambdaBasicExecutionRole-autoscaleElasticache",
            "arn:aws:iam::1234:policy/AWSLambdaBasicExecutionRole-autoscaleElasticache/statement/2",
        ),
        (
            "arn:aws:iam::aws:policy/AWSLambdaFullAccess",
            "arn:aws:iam::aws:policy/AWSLambdaFullAccess/statement/1",
        ),
        (
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole/statement/1",
        ),
        (
            "arn:aws:iam::aws:policy/service-role/AWSLambdaRole",
            "arn:aws:iam::aws:policy/service-role/AWSLambdaRole/statement/1",
        ),
        (
            "arn:aws:iam::aws:policy/AmazonElastiCacheFullAccess",
            "arn:aws:iam::aws:policy/AmazonElastiCacheFullAccess/statement/1",
        ),
        (
            "arn:aws:iam::aws:policy/AmazonElastiCacheFullAccess",
            "arn:aws:iam::aws:policy/AmazonElastiCacheFullAccess/statement/2",
        ),
        # Group policy statements
        (
            "arn:aws:iam::1234:group/example-group-0/inline_policy/group_inline_policy",
            "arn:aws:iam::1234:group/example-group-0/inline_policy/group_inline_policy/statement/VisualEditor0",
        ),
        (
            "arn:aws:iam::1234:group/example-group-0/inline_policy/group_inline_policy",
            "arn:aws:iam::1234:group/example-group-0/inline_policy/group_inline_policy/statement/VisualEditor1",
        ),
        (
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess/statement/1",
        ),
        (
            "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess",
            "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess/statement/1",
        ),
        (
            "arn:aws:iam::1234:group/example-group-1/inline_policy/admin_policy",
            "arn:aws:iam::1234:group/example-group-1/inline_policy/admin_policy/statement/1",
        ),
    }

    # Assert: Check that access key nodes were created
    assert check_nodes(
        neo4j_session,
        "AccountAccessKey",
        ["accesskeyid", "id"],
    ) == {
        ("AKIAIOSFODNN7EXAMPLE", "AKIAIOSFODNN7EXAMPLE"),
        ("AKIAI44QH8DHBEXAMPLE", "AKIAI44QH8DHBEXAMPLE"),
        ("AKIAJQ5CMEXAMPLE", "AKIAJQ5CMEXAMPLE"),
        ("AKIAEXAMPLE123", "AKIAEXAMPLE123"),
    }

    # Assert: Check that relationships were created between access keys and users
    assert check_rels(
        neo4j_session,
        "AccountAccessKey",
        "accesskeyid",
        "AWSUser",
        "arn",
        "AWS_ACCESS_KEY",
        rel_direction_right=False,
    ) == {
        ("AKIAIOSFODNN7EXAMPLE", "arn:aws:iam::1234:user/user1"),
        ("AKIAI44QH8DHBEXAMPLE", "arn:aws:iam::1234:user/user1"),
        ("AKIAJQ5CMEXAMPLE", "arn:aws:iam::1234:user/user2"),
        ("AKIAEXAMPLE123", "arn:aws:iam::1234:user/user3"),
    }

    # Assert: Check that service-specific credential nodes were created
    assert check_nodes(
        neo4j_session,
        "AWSServiceSpecificCredential",
        ["service_specific_credential_id", "service_name", "status"],
    ) == {
        ("ANPAEXAMPLEUSER1A", "codecommit.amazonaws.com", "Active"),
        ("ANPAEXAMPLEUSER1B", "bedrock.amazonaws.com", "Inactive"),
        ("ANPAEXAMPLEUSER2A", "codecommit.amazonaws.com", "Active"),
    }

    # Assert: Check that relationships were created between users and service-specific credentials
    assert check_rels(
        neo4j_session,
        "AWSServiceSpecificCredential",
        "service_specific_credential_id",
        "AWSUser",
        "arn",
        "SERVICE_SPECIFIC_CREDENTIAL",
        rel_direction_right=False,
    ) == {
        ("ANPAEXAMPLEUSER1A", "arn:aws:iam::1234:user/user1"),
        ("ANPAEXAMPLEUSER1B", "arn:aws:iam::1234:user/user1"),
        ("ANPAEXAMPLEUSER2A", "arn:aws:iam::1234:user/user2"),
    }

    # Assert: Check account RESOURCE relationships to service-specific credentials
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSServiceSpecificCredential",
        "service_specific_credential_id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "ANPAEXAMPLEUSER1A"),
        (TEST_ACCOUNT_ID, "ANPAEXAMPLEUSER1B"),
        (TEST_ACCOUNT_ID, "ANPAEXAMPLEUSER2A"),
    }


@patch.object(
    cartography.intel.aws.iam,
    "get_user_service_specific_credentials_data",
    side_effect=[
        GET_USER_SERVICE_SPECIFIC_CREDENTIALS_DATA,
        {
            "arn:aws:iam::1234:user/user1": [],
            "arn:aws:iam::1234:user/user2": [],
            "arn:aws:iam::1234:user/user3": [],
        },
    ],
)
def test_sync_user_service_specific_credentials_cleanup(
    mock_get_user_service_specific_credentials_data,
    neo4j_session,
):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Seed users because sync_user_service_specific_credentials queries existing AWSUser nodes.
    users = cartography.intel.aws.iam.transform_users(GET_USER_LIST_DATA["Users"])
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        users,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.aws.iam.sync_user_service_specific_credentials(
        neo4j_session,
        boto3_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "AWSServiceSpecificCredential",
        ["service_specific_credential_id"],
    ) == {
        ("ANPAEXAMPLEUSER1A",),
        ("ANPAEXAMPLEUSER1B",),
        ("ANPAEXAMPLEUSER2A",),
    }

    # Re-sync with empty credentials and a new update tag; stale credentials should be cleaned up.
    cartography.intel.aws.iam.sync_user_service_specific_credentials(
        neo4j_session,
        boto3_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG_2,
        {"UPDATE_TAG": TEST_UPDATE_TAG_2, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert (
        check_nodes(
            neo4j_session,
            "AWSServiceSpecificCredential",
            ["service_specific_credential_id"],
        )
        == set()
    )

    assert (
        check_rels(
            neo4j_session,
            "AWSServiceSpecificCredential",
            "service_specific_credential_id",
            "AWSUser",
            "arn",
            "SERVICE_SPECIFIC_CREDENTIAL",
            rel_direction_right=False,
        )
        == set()
    )

    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "AWSServiceSpecificCredential",
            "service_specific_credential_id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == set()
    )
