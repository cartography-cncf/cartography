from unittest import mock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.iam
import cartography.intel.aws.permission_relationships
import tests.data.aws.iam
from cartography.cli import CLI
from cartography.config import Config
from cartography.intel.aws.iam import sync
from cartography.sync import build_default_sync
from tests.data.aws.iam import LIST_GROUPS
from tests.data.aws.iam.role_policies import (
    ANOTHER_GET_ROLE_LIST_DATASET as GET_ROLE_LIST_DATA,
)
from tests.data.aws.iam.role_policies import GET_ROLE_MANAGED_POLICY_DATA
from tests.data.aws.iam.user_policies import GET_USER_LIST_DATA
from tests.data.aws.iam.user_policies import GET_USER_MANAGED_POLS_SAMPLE
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

# Create inline policy data that matches the roles in ANOTHER_GET_ROLE_LIST_DATASET
GET_ROLE_INLINE_POLS_SAMPLE = {
    "arn:aws:iam::1234:role/ServiceRole": {
        "ServiceRole": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "iam:ListPolicies",
                    "iam:GetAccountSummary",
                    "iam:ListAccountAliases",
                    "iam:GenerateServiceLastAccessedDetails",
                    "iam:ListRoles",
                    "iam:ListUsers",
                    "iam:ListGroups",
                    "iam:GetServiceLastAccessedDetails",
                    "iam:ListRolePolicies",
                ],
                "Resource": "*",
            },
        ],
    },
    "arn:aws:iam::1234:role/ElasticacheAutoscale": {},
    "arn:aws:iam::1234:role/sftp-LambdaExecutionRole-1234": {},
}

# Create group policy data that matches the groups in LIST_GROUPS
GET_GROUP_INLINE_POLS_SAMPLE = {
    "arn:aws:iam::000000000000:group/example-group-0": {
        "group_inline_policy": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject",
                ],
                "Resource": [
                    "arn:aws:s3:::example-bucket",
                    "arn:aws:s3:::example-bucket/*",
                ],
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstances",
                    "ec2:DescribeSecurityGroups",
                ],
                "Resource": "*",
            },
        ],
    },
    "arn:aws:iam::000000000000:group/example-group-1": {
        "admin_policy": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*",
            },
        ],
    },
}

GET_GROUP_MANAGED_POLICY_DATA = {
    "arn:aws:iam::000000000000:group/example-group-0": {
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                ],
                "Resource": "*",
            },
        ],
        "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess": [
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:Describe*",
                    "elasticloadbalancing:Describe*",
                ],
                "Resource": "*",
            },
        ],
    },
    "arn:aws:iam::000000000000:group/example-group-1": {
        "arn:aws:iam::aws:policy/AdministratorAccess": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*",
            },
        ],
    },
}

# Create user inline policy data
GET_USER_INLINE_POLS_SAMPLE = {
    "arn:aws:iam::1234:user/user1": {
        "user1_inline_policy": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:DeleteItem",
                ],
                "Resource": "arn:aws:dynamodb:us-east-1:1234:table/user1-table",
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                ],
                "Resource": "arn:aws:s3:::user1-bucket/*",
            },
        ],
    },
    "arn:aws:iam::1234:user/user2": {
        "user2_admin_policy": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*",
            },
        ],
    },
    "arn:aws:iam::1234:user/user3": {},
}


TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_permission_relationships_file_arguments():
    """
    Test that we correctly read arguments for --permission-relationships-file
    """
    # Test the correct field is set in the Cartography config object
    fname = "/some/test/file.yaml"
    config = Config(
        neo4j_uri="bolt://thisdoesnotmatter:1234",
        permission_relationships_file=fname,
    )
    assert config.permission_relationships_file == fname

    # Test the correct field is set in the Cartography CLI object
    argv = ["--permission-relationships-file", "/some/test/file.yaml"]
    cli_object = CLI(build_default_sync(), prog="cartography")
    cli_parsed_output = cli_object.parser.parse_args(argv)
    assert cli_parsed_output.permission_relationships_file == "/some/test/file.yaml"

    # Test that the default RPR file is set if --permission-relationships-file is not set in the CLI
    argv = []
    cli_object = CLI(build_default_sync(), prog="cartography")
    cli_parsed_output = cli_object.parser.parse_args(argv)
    assert (
        cli_parsed_output.permission_relationships_file
        == "cartography/data/permission_relationships.yaml"
    )


def _create_base_account(neo4j_session):
    neo4j_session.run("MERGE (a:AWSAccount{id:$AccountId})", AccountId=TEST_ACCOUNT_ID)


def test_load_users(neo4j_session):
    _create_base_account(neo4j_session)
    data = tests.data.aws.iam.LIST_USERS["Users"]

    cartography.intel.aws.iam.load_users(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_load_groups(neo4j_session):
    data = tests.data.aws.iam.LIST_GROUPS["Groups"]

    cartography.intel.aws.iam.load_groups(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def _get_principal_role_nodes(neo4j_session):
    """
    Get AWSPrincipal node tuples (rolearn, arn) that have arns with substring `:role/`
    """
    return {
        (roleid, arn)
        for (roleid, arn) in check_nodes(
            neo4j_session,
            "AWSPrincipal",
            ["roleid", "arn"],
        )
        if ":role/"
        in arn  # filter out other Principals nodes, like the ec2 service princiapl
    }


def test_load_roles(neo4j_session):
    """
    Ensures that we load AWSRoles without duplicating against AWSPrincipal nodes
    """
    # Arrange
    assert set() == _get_principal_role_nodes(neo4j_session)
    data = tests.data.aws.iam.LIST_ROLES["Roles"]
    expected_principals = {  # (roleid, arn)
        (None, "arn:aws:iam::000000000000:role/example-role-0"),
        (None, "arn:aws:iam::000000000000:role/example-role-1"),
        (None, "arn:aws:iam::000000000000:role/example-role-2"),
        (None, "arn:aws:iam::000000000000:role/example-role-3"),
    }
    # Act: Load the roles as bare Principals without other labels. This replicates the case where we discover a
    # role from another account via an AssumeRolePolicy document or similar ways. See #1133.
    neo4j_session.run(
        """
        UNWIND $data as item
            MERGE (p:AWSPrincipal{arn: item.Arn})
        """,
        data=data,
    )
    actual_principals = _get_principal_role_nodes(neo4j_session)
    # Assert
    assert expected_principals == actual_principals
    assert set() == check_nodes(neo4j_session, "AWSRole", ["arn"])
    # Arrange
    expected_nodes = {  # (roleid, arn)
        ("AROA00000000000000000", "arn:aws:iam::000000000000:role/example-role-0"),
        ("AROA00000000000000001", "arn:aws:iam::000000000000:role/example-role-1"),
        ("AROA00000000000000002", "arn:aws:iam::000000000000:role/example-role-2"),
        ("AROA00000000000000003", "arn:aws:iam::000000000000:role/example-role-3"),
    }
    # Act: Load the roles normally
    cartography.intel.aws.iam.load_roles(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    # Ensure that the new AWSRoles are merged into pre-existing AWSPrincipal nodes,
    # and we do not have duplicate AWSPrincipal nodes.
    role_nodes = check_nodes(neo4j_session, "AWSRole", ["roleid", "arn"])
    principal_nodes = _get_principal_role_nodes(neo4j_session)
    assert expected_nodes == role_nodes
    assert expected_nodes == principal_nodes


def test_load_roles_creates_trust_relationships(neo4j_session):
    data = tests.data.aws.iam.LIST_ROLES["Roles"]

    cartography.intel.aws.iam.load_roles(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Get TRUSTS_AWS_PRINCIPAL relationships from Neo4j.
    result = neo4j_session.run(
        """
        MATCH (n1:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(n2:AWSPrincipal) RETURN n1.arn, n2.arn;
        """,
    )

    # Define the relationships we expect in terms of role ARN and principal ARN.
    expected = {
        (
            "arn:aws:iam::000000000000:role/example-role-0",
            "arn:aws:iam::000000000000:root",
        ),
        (
            "arn:aws:iam::000000000000:role/example-role-1",
            "arn:aws:iam::000000000000:role/example-role-0",
        ),
        ("arn:aws:iam::000000000000:role/example-role-2", "ec2.amazonaws.com"),
        (
            "arn:aws:iam::000000000000:role/example-role-3",
            "arn:aws:iam::000000000000:saml-provider/ADFS",
        ),
    }
    # Transform the results of our query above to match the format of our expectations.
    actual = {(r["n1.arn"], r["n2.arn"]) for r in result}
    # Compare our actual results to our expected results.
    assert actual == expected


def test_load_inline_policy(neo4j_session):
    cartography.intel.aws.iam.load_policy(
        neo4j_session,
        "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
        "group_inline_policy",
        "inline",
        "arn:aws:iam::000000000000:group/example-group-0",
        TEST_UPDATE_TAG,
    )


def test_load_inline_policy_data(neo4j_session):
    cartography.intel.aws.iam.load_policy_statements(
        neo4j_session,
        "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
        "group_inline_policy",
        tests.data.aws.iam.INLINE_POLICY_STATEMENTS,
        TEST_UPDATE_TAG,
    )


def test_map_permissions(neo4j_session):
    # Insert an s3 bucket to map
    neo4j_session.run(
        """
    MERGE (s3:S3Bucket{arn:'arn:aws:s3:::test_bucket'})<-[:RESOURCE]-(a:AWSAccount{id:$AccountId})
    """,
        AccountId=TEST_ACCOUNT_ID,
    )

    cartography.intel.aws.permission_relationships.sync(
        neo4j_session,
        mock.MagicMock,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "permission_relationships_file": "cartography/data/permission_relationships.yaml",
        },
    )
    results = neo4j_session.run(
        "MATCH ()-[r:CAN_READ]->() RETURN count(r) as rel_count",
    )
    assert results
    for result in results:
        assert result["rel_count"] == 1


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
    cartography.intel.aws.iam, "get_group_list_data", return_value=LIST_GROUPS
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
def test_sync_iam(
    mock_get_users,
    mock_get_user_inline_pols,
    mock_get_user_managed_pols,
    mock_get_groups,
    mock_get_group_policies,
    mock_get_group_managed_pols,
    mock_get_roles,
    mock_get_role_policies,
    mock_get_role_managed_pols,
    neo4j_session,
):
    """Test IAM sync end-to-end"""
    # Arrange
    boto3_session = MagicMock()
    neo4j_session.run("MATCH (n) DETACH DELETE n")
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
    # AWSAccount -> AWSPrincipal
    expected_account_principal = {
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:user/user1"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:user/user2"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:user/user3"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:role/ServiceRole"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:role/ElasticacheAutoscale"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::1234:role/sftp-LambdaExecutionRole-1234"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::000000000000:group/example-group-0"),
        (TEST_ACCOUNT_ID, "arn:aws:iam::000000000000:group/example-group-1"),
        # Additional principals from trust relationships
        ("54321", "arn:aws:iam::54321:root"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "AWSPrincipal",
            "arn",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_account_principal
    )

    # AWSPrincipal -> AWSPolicy
    expected_principal_policy = {
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
            "arn:aws:iam::000000000000:group/example-group-0",
            "arn:aws:iam::000000000000:group/example-group-0/inline_policy/group_inline_policy",
        ),
        (
            "arn:aws:iam::000000000000:group/example-group-0",
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
        ),
        (
            "arn:aws:iam::000000000000:group/example-group-0",
            "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess",
        ),
        (
            "arn:aws:iam::000000000000:group/example-group-1",
            "arn:aws:iam::000000000000:group/example-group-1/inline_policy/admin_policy",
        ),
        (
            "arn:aws:iam::000000000000:group/example-group-1",
            "arn:aws:iam::aws:policy/AdministratorAccess",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSPrincipal",
            "arn",
            "AWSPolicy",
            "id",
            "POLICY",
            rel_direction_right=True,
        )
        == expected_principal_policy
    )

    # AWSPolicy -> AWSPolicyStatement
    expected_policy_statement = {
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
            "arn:aws:iam::000000000000:group/example-group-0/inline_policy/group_inline_policy",
            "arn:aws:iam::000000000000:group/example-group-0/inline_policy/group_inline_policy/statement/VisualEditor0",
        ),
        (
            "arn:aws:iam::000000000000:group/example-group-0/inline_policy/group_inline_policy",
            "arn:aws:iam::000000000000:group/example-group-0/inline_policy/group_inline_policy/statement/VisualEditor1",
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
            "arn:aws:iam::000000000000:group/example-group-1/inline_policy/admin_policy",
            "arn:aws:iam::000000000000:group/example-group-1/inline_policy/admin_policy/statement/1",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSPolicy",
            "id",
            "AWSPolicyStatement",
            "id",
            "STATEMENT",
            rel_direction_right=True,
        )
        == expected_policy_statement
    )
