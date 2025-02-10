from unittest import mock

import cartography.intel.aws.iam
import cartography.intel.aws.permission_relationships
import tests.data.aws.iam
from cartography.cli import CLI
from cartography.config import Config
from cartography.sync import build_default_sync
from tests.integration.util import check_nodes

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
