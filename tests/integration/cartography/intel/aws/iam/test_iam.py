from unittest import mock
from unittest.mock import MagicMock

import cartography.intel.aws.iam
import cartography.intel.aws.permission_relationships
import tests.data.aws.iam
from cartography.cli import CLI
from cartography.client.core.tx import load
from cartography.config import Config
from cartography.intel.aws.iam import _transform_policy_statements
from cartography.intel.aws.iam import sync_root_principal
from cartography.models.aws.iam.inline_policy import AWSInlinePolicySchema
from cartography.sync import build_default_sync
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

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
    # Hack to create the root principal node since we're not calling the full sync() function in this test.
    sync_root_principal(
        neo4j_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_load_users(neo4j_session):
    _create_base_account(neo4j_session)
    user_data = cartography.intel.aws.iam.transform_users(
        tests.data.aws.iam.LIST_USERS["Users"]
    )
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        user_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def test_load_groups(neo4j_session):
    # Create a mock boto3 session for the test
    mock_boto3_session = MagicMock()
    mock_boto3_session.client.return_value.get_group.return_value = {"Users": []}

    # Get group memberships
    group_memberships = cartography.intel.aws.iam.get_group_memberships(
        mock_boto3_session, tests.data.aws.iam.LIST_GROUPS["Groups"]
    )

    # Transform groups with membership data
    group_data = cartography.intel.aws.iam.transform_groups(
        tests.data.aws.iam.LIST_GROUPS["Groups"], group_memberships
    )

    cartography.intel.aws.iam.load_groups(
        neo4j_session,
        group_data,
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


def test_load_roles_creates_trust_relationships(neo4j_session):
    cartography.intel.aws.iam.sync_role_assumptions(
        neo4j_session,
        tests.data.aws.iam.LIST_ROLES,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert: Get TRUSTS_AWS_PRINCIPAL relationships from Neo4j using check_rels.
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

    actual = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "AWSPrincipal",
        "arn",
        "TRUSTS_AWS_PRINCIPAL",
    )

    assert actual == expected


def test_load_inline_policy(neo4j_session):
    # Just load in a single policy.
    inline_policy_data = [
        {
            "id": "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
            "arn": None,  # Inline policies don't have arns
            "name": "group_inline_policy",
            "type": "inline",
            "principal_arns": ["arn:aws:iam::000000000000:group/example-group-0"],
        }
    ]
    load(
        neo4j_session,
        AWSInlinePolicySchema(),
        inline_policy_data,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )


def test_load_inline_policy_data(neo4j_session):
    transformed_stmts = _transform_policy_statements(
        tests.data.aws.iam.INLINE_POLICY_STATEMENTS,
        "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
    )
    cartography.intel.aws.iam.load_policy_statements(
        neo4j_session,
        transformed_stmts,
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
