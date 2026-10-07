from contextlib import ExitStack
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.aws.iam
from cartography.intel.aws.iam import AccountAuthorizationDetails
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
from tests.data.aws.iam.user_inline_policies import GET_USER_INLINE_POLS_SAMPLE
from tests.data.aws.iam.user_policies import GET_USER_LIST_DATA
from tests.data.aws.iam.user_policies import GET_USER_MANAGED_POLS_SAMPLE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "1234"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.iam,
    "get_account_authorization_details",
    return_value=None,
)
@patch.object(
    cartography.intel.aws.iam,
    "get_server_certificates",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.iam,
    "get_saml_providers",
    return_value=[],
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
def test_sync_iam(
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
    mock_get_account_authorization_details,
    neo4j_session,
):
    """Test IAM sync end-to-end through the per-principal fallback path"""
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
    # Users, groups and roles resolve managed policies through one shared cache
    user_cache = mock_get_user_managed_policy_data.call_args.args[2]
    assert isinstance(user_cache, dict)
    assert mock_get_group_managed_policy_data.call_args.args[2] is user_cache
    assert mock_get_role_managed_policy_data.call_args.args[2] is user_cache

    _assert_iam_graph(neo4j_session)


def _assert_iam_graph(neo4j_session):
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
    expected_group_membership = {
        ("arn:aws:iam::1234:user/user1", "arn:aws:iam::1234:group/example-group-0"),
        ("arn:aws:iam::1234:user/user2", "arn:aws:iam::1234:group/example-group-0"),
        ("arn:aws:iam::1234:user/user3", "arn:aws:iam::1234:group/example-group-1"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSUser",
            "arn",
            "AWSGroup",
            "arn",
            "MEMBER_AWS_GROUP",
            rel_direction_right=True,
        )
        == expected_group_membership
    )
    # Canonical ontology edge: (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
    assert (
        check_rels(
            neo4j_session,
            "AWSUser",
            "arn",
            "AWSGroup",
            "arn",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_group_membership
    )

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
        "AWSAccountAccessKey",
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
        "AWSAccountAccessKey",
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

    # Canonical ontology edge: (:APIKey)-[:OWNED_BY]->(:UserAccount)
    assert check_rels(
        neo4j_session,
        "AWSAccountAccessKey",
        "accesskeyid",
        "AWSUser",
        "arn",
        "OWNED_BY",
        rel_direction_right=True,
    ) == {
        ("AKIAIOSFODNN7EXAMPLE", "arn:aws:iam::1234:user/user1"),
        ("AKIAI44QH8DHBEXAMPLE", "arn:aws:iam::1234:user/user1"),
        ("AKIAJQ5CMEXAMPLE", "arn:aws:iam::1234:user/user2"),
        ("AKIAEXAMPLE123", "arn:aws:iam::1234:user/user3"),
    }


GOV_ACCOUNT_ID = "111122223333"
GOV_EXTERNAL_ACCOUNT_ID = "444455556666"
GOV_ROLE_LIST_DATA = {
    "Roles": [
        {
            "Path": "/",
            "RoleName": "ExampleCrossAccountRole",
            "RoleId": "AROAEXAMPLEGOVROLE1",
            "Arn": f"arn:aws-us-gov:iam::{GOV_ACCOUNT_ID}:role/ExampleCrossAccountRole",
            "CreateDate": datetime(2024, 1, 15, 10, 30, 15),
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": [
                                f"arn:aws-us-gov:iam::{GOV_ACCOUNT_ID}:root",
                                f"arn:aws-us-gov:iam::{GOV_EXTERNAL_ACCOUNT_ID}:root",
                            ],
                        },
                        "Action": "sts:AssumeRole",
                    },
                ],
            },
            "MaxSessionDuration": 3600,
        },
    ],
}
# IAM getters that the GovCloud tests stub to empty results. Only roles carry data.
_EMPTY_IAM_GETTERS: dict[str, Any] = {
    # None takes the per-principal fallback, which the getters below stub.
    "get_account_authorization_details": None,
    "get_account_summary": {},
    "get_server_certificates": [],
    "get_saml_providers": [],
    "get_group_memberships": {},
    "get_role_managed_policy_data": {},
    "get_role_policy_data": {},
    "get_group_managed_policy_data": {},
    "get_group_policy_data": {},
    "get_group_list_data": {"Groups": []},
    "get_user_managed_policy_data": {},
    "get_user_policy_data": {},
    "get_user_list_data": {"Users": []},
    "get_user_access_keys_data": {},
}


@pytest.fixture
def govcloud_iam_roles(neo4j_session):
    """Stub the IAM API and return the mock for the role list."""
    with ExitStack() as stack:
        for name, value in _EMPTY_IAM_GETTERS.items():
            stack.enter_context(
                patch.object(cartography.intel.aws.iam, name, return_value=value)
            )
        stack.enter_context(
            patch.object(
                cartography.intel.aws.iam, "sync_service_last_accessed_details"
            )
        )
        yield stack.enter_context(
            patch.object(cartography.intel.aws.iam, "get_role_list_data")
        )
    # The graph is only wiped at module teardown, and test_sync_iam checks the principals
    # of every account, so remove the GovCloud accounts and their principals here.
    neo4j_session.run(
        "MATCH (a:AWSAccount) WHERE a.id IN $ids "
        "OPTIONAL MATCH (a)-[:RESOURCE]->(p:AWSPrincipal) DETACH DELETE a, p",
        ids=[GOV_ACCOUNT_ID, GOV_EXTERNAL_ACCOUNT_ID],
    )


def _sync_govcloud_iam(neo4j_session, account_id, update_tag):
    sync(
        neo4j_session,
        MagicMock(),
        ["us-gov-west-1", "us-gov-east-1"],
        account_id,
        update_tag,
        {"UPDATE_TAG": update_tag, "AWS_ID": account_id},
    )


def _root_principals(neo4j_session, account_id):
    return {
        record["arn"]
        for record in neo4j_session.run(
            "MATCH (:AWSAccount {id: $account_id})-[:RESOURCE]->(r:AWSRootPrincipal) "
            "RETURN r.arn AS arn",
            account_id=account_id,
        )
    }


def test_sync_iam_govcloud_root_trust(govcloud_iam_roles, neo4j_session):
    """
    In AWS GovCloud (US), trust policies name account roots as "arn:aws-us-gov:iam::<account>:root".
    The root principal nodes must use the same partition, so the trust edges form.
    """
    # Arrange
    neo4j_session.run("MATCH (n:AWSPrincipal) DETACH DELETE n")
    govcloud_iam_roles.return_value = GOV_ROLE_LIST_DATA
    create_test_account(neo4j_session, GOV_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    _sync_govcloud_iam(neo4j_session, GOV_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Assert
    assert check_nodes(neo4j_session, "AWSRootPrincipal", ["arn"]) == {
        (f"arn:aws-us-gov:iam::{GOV_ACCOUNT_ID}:root",),
        (f"arn:aws-us-gov:iam::{GOV_EXTERNAL_ACCOUNT_ID}:root",),
    }
    assert check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "AWSRootPrincipal",
        "arn",
        "TRUSTS_AWS_PRINCIPAL",
        rel_direction_right=True,
    ) == {
        (
            f"arn:aws-us-gov:iam::{GOV_ACCOUNT_ID}:role/ExampleCrossAccountRole",
            f"arn:aws-us-gov:iam::{GOV_ACCOUNT_ID}:root",
        ),
        (
            f"arn:aws-us-gov:iam::{GOV_ACCOUNT_ID}:role/ExampleCrossAccountRole",
            f"arn:aws-us-gov:iam::{GOV_EXTERNAL_ACCOUNT_ID}:root",
        ),
    }


def test_sync_iam_removes_stale_root_principal(govcloud_iam_roles, neo4j_session):
    """
    An older sync built GovCloud root principals with the commercial partition. The next
    sync replaces that node with the aws-us-gov one instead of keeping both.
    """
    # Arrange
    neo4j_session.run("MATCH (n:AWSPrincipal) DETACH DELETE n")
    govcloud_iam_roles.return_value = GOV_ROLE_LIST_DATA
    create_test_account(neo4j_session, GOV_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.iam.sync_root_principal(
        neo4j_session,
        GOV_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        "aws",
    )
    new_update_tag = TEST_UPDATE_TAG + 1
    create_test_account(neo4j_session, GOV_ACCOUNT_ID, new_update_tag)

    # Act
    _sync_govcloud_iam(neo4j_session, GOV_ACCOUNT_ID, new_update_tag)

    # Assert
    assert _root_principals(neo4j_session, GOV_ACCOUNT_ID) == {
        f"arn:aws-us-gov:iam::{GOV_ACCOUNT_ID}:root",
    }


def test_sync_iam_root_principal_cleanup_keeps_other_accounts(
    govcloud_iam_roles,
    neo4j_session,
):
    """
    The root principal cleanup is scoped to the synced account, so it keeps the root of
    an account that an earlier run synced and this run does not.
    """
    # Arrange
    neo4j_session.run("MATCH (n:AWSPrincipal) DETACH DELETE n")
    govcloud_iam_roles.return_value = {"Roles": []}
    create_test_account(neo4j_session, GOV_EXTERNAL_ACCOUNT_ID, TEST_UPDATE_TAG)
    _sync_govcloud_iam(neo4j_session, GOV_EXTERNAL_ACCOUNT_ID, TEST_UPDATE_TAG)
    new_update_tag = TEST_UPDATE_TAG + 1
    create_test_account(neo4j_session, GOV_ACCOUNT_ID, new_update_tag)

    # Act
    _sync_govcloud_iam(neo4j_session, GOV_ACCOUNT_ID, new_update_tag)

    # Assert
    assert _root_principals(neo4j_session, GOV_EXTERNAL_ACCOUNT_ID) == {
        f"arn:aws-us-gov:iam::{GOV_EXTERNAL_ACCOUNT_ID}:root",
    }


def test_sync_iam_keeps_trusted_root_of_other_synced_account(
    govcloud_iam_roles,
    neo4j_session,
):
    """
    Two accounts are synced in one run, and a role in the first trusts the second account's
    root. The root principal cleanup of each account keeps both roots and the trust edge.
    """
    # Arrange
    neo4j_session.run("MATCH (n:AWSPrincipal) DETACH DELETE n")
    create_test_account(neo4j_session, GOV_ACCOUNT_ID, TEST_UPDATE_TAG)
    create_test_account(neo4j_session, GOV_EXTERNAL_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    for account_id, roles in (
        (GOV_ACCOUNT_ID, GOV_ROLE_LIST_DATA),
        (GOV_EXTERNAL_ACCOUNT_ID, {"Roles": []}),
    ):
        govcloud_iam_roles.return_value = roles
        _sync_govcloud_iam(neo4j_session, account_id, TEST_UPDATE_TAG)

    # Assert
    assert _root_principals(neo4j_session, GOV_ACCOUNT_ID) == {
        f"arn:aws-us-gov:iam::{GOV_ACCOUNT_ID}:root",
    }
    assert _root_principals(neo4j_session, GOV_EXTERNAL_ACCOUNT_ID) == {
        f"arn:aws-us-gov:iam::{GOV_EXTERNAL_ACCOUNT_ID}:root",
    }
    assert (
        f"arn:aws-us-gov:iam::{GOV_ACCOUNT_ID}:role/ExampleCrossAccountRole",
        f"arn:aws-us-gov:iam::{GOV_EXTERNAL_ACCOUNT_ID}:root",
    ) in check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "AWSRootPrincipal",
        "arn",
        "TRUSTS_AWS_PRINCIPAL",
        rel_direction_right=True,
    )


@patch.object(
    cartography.intel.aws.iam,
    "get_account_authorization_details",
    return_value=AccountAuthorizationDetails(
        user_inline_policies=GET_USER_INLINE_POLS_SAMPLE,
        user_managed_policies=GET_USER_MANAGED_POLS_SAMPLE,
        group_inline_policies=GET_GROUP_INLINE_POLS_SAMPLE,
        group_managed_policies=GET_GROUP_MANAGED_POLICY_DATA,
        group_memberships=GET_GROUP_MEMBERSHIPS_DATA,
        role_inline_policies=GET_ROLE_INLINE_POLS_SAMPLE,
        role_managed_policies=GET_ROLE_MANAGED_POLICY_DATA,
    ),
)
@patch.object(cartography.intel.aws.iam, "get_server_certificates", return_value=[])
@patch.object(cartography.intel.aws.iam, "get_saml_providers", return_value=[])
@patch.object(cartography.intel.aws.iam, "sync_service_last_accessed_details")
@patch.object(
    cartography.intel.aws.iam, "get_role_list_data", return_value=GET_ROLE_LIST_DATA
)
@patch.object(
    cartography.intel.aws.iam, "get_group_list_data", return_value=LIST_GROUPS_SAMPLE
)
@patch.object(
    cartography.intel.aws.iam, "get_user_list_data", return_value=GET_USER_LIST_DATA
)
@patch.object(
    cartography.intel.aws.iam,
    "get_user_access_keys_data",
    return_value=GET_USER_ACCESS_KEYS_DATA,
)
def test_sync_iam_from_account_authorization_details(
    mock_get_user_access_keys,
    mock_get_user_list_data,
    mock_get_group_list_data,
    mock_get_role_list_data,
    mock_sync_service_last_accessed_details,
    mock_get_saml_providers,
    mock_get_server_certificates,
    mock_get_account_authorization_details,
    neo4j_session,
):
    """The GetAccountAuthorizationDetails path builds the same graph without per-principal calls."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    per_principal_getters = [
        "get_user_policy_data",
        "get_user_managed_policy_data",
        "get_group_policy_data",
        "get_group_managed_policy_data",
        "get_group_memberships",
        "get_role_policy_data",
        "get_role_managed_policy_data",
    ]
    patches = [
        patch.object(
            cartography.intel.aws.iam,
            name,
            side_effect=AssertionError(f"{name} should not be called"),
        )
        for name in per_principal_getters
    ]
    for p in patches:
        p.start()
    try:
        create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
        sync(
            neo4j_session,
            MagicMock(),
            ["us-east-1"],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )
    finally:
        for p in patches:
            p.stop()

    _assert_iam_graph(neo4j_session)
