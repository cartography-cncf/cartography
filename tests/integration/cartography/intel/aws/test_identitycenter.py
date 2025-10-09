import tests.data.aws.identitycenter
from cartography.client.core.tx import load
from cartography.intel.aws.identitycenter import load_identity_center_instances
from cartography.intel.aws.identitycenter import load_permission_sets
from cartography.intel.aws.identitycenter import load_role_assignments
from cartography.intel.aws.identitycenter import load_sso_groups
from cartography.intel.aws.identitycenter import load_sso_users
from cartography.intel.aws.identitycenter import transform_sso_groups
from cartography.intel.aws.identitycenter import transform_sso_users
from cartography.models.aws.identitycenter.awspermissionset import (
    RoleAssignmentAllowedByGroupMatchLink,
)
from cartography.models.aws.identitycenter.awssogroup import AWSSSOGroupSchema
from cartography.models.aws.identitycenter.awsssouser import AWSSSOUserSchema
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "1234567890"


def test_load_sso_users(neo4j_session):
    """Test loading SSO users into Neo4j."""
    # Use predefined data from tests.data.aws.identitycenter
    users = tests.data.aws.identitycenter.LIST_USERS

    # Load SSO users into the Neo4j session
    load_sso_users(
        neo4j_session,
        transform_sso_users(users),
        "d-1234567890",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    # Use check_nodes to verify that the SSO users are correctly loaded
    assert check_nodes(neo4j_session, "AWSSSOUser", ["id", "external_id"]) == {
        ("aaaaaaaa-a0d1-aaac-5af0-59c813ec7671", "00aaaaabbbbb")
    }


def test_load_sso_groups(neo4j_session):
    """Test loading SSO groups into Neo4j."""
    groups = tests.data.aws.identitycenter.LIST_GROUPS

    load_sso_groups(
        neo4j_session,
        transform_sso_groups(groups),
        "d-1234567890",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    assert check_nodes(neo4j_session, "AWSSSOGroup", ["id", "external_id"]) == {
        ("gggggggg-a0d1-aaac-5af0-59c813ec7671", "00ggggghhhhh")
    }


def test_load_identity_center_instances(neo4j_session):
    """Test loading Identity Center instances into Neo4j."""
    # Use predefined data from tests.data.aws.identitycenter
    instances = tests.data.aws.identitycenter.LIST_INSTANCES

    # Load Identity Center instances into the Neo4j session
    load_identity_center_instances(
        neo4j_session,
        instances,
        "us-west-2",
        "123456789012",
        TEST_ACCOUNT_ID,
    )

    # Verify that the instances are correctly loaded
    assert check_nodes(
        neo4j_session, "AWSIdentityCenter", ["id", "identity_store_id"]
    ) == {
        ("arn:aws:sso:::instance/ssoins-12345678901234567", "d-1234567890"),
    }


def test_load_permission_sets(neo4j_session):
    """Test loading Identity Center permission sets into Neo4j."""
    # Use predefined data from tests.data.aws.identitycenter
    permission_sets = tests.data.aws.identitycenter.LIST_PERMISSION_SETS

    # Load permission sets into the Neo4j session
    load_permission_sets(
        neo4j_session,
        permission_sets,
        "arn:aws:sso:::instance/ssoins-12345678901234567",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    # Verify that the permission sets are correctly loaded
    assert check_nodes(neo4j_session, "AWSPermissionSet", ["id", "name"]) == {
        (
            "arn:aws:sso:::permissionSet/ssoins-12345678901234567/ps-12345678901234567",
            "AdministratorAccess",
        ),
    }


def test_link_sso_group_to_permission_set(neo4j_session):
    """Test linking SSO groups to permission sets using standard relationships."""
    groups = tests.data.aws.identitycenter.LIST_GROUPS
    permission_sets = tests.data.aws.identitycenter.LIST_PERMISSION_SETS

    # Load base nodes first
    load_sso_groups(
        neo4j_session,
        transform_sso_groups(groups),
        "d-1234567890",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )
    load_permission_sets(
        neo4j_session,
        permission_sets,
        "arn:aws:sso:::instance/ssoins-12345678901234567",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    # Create mapping data to attach relationships
    group = groups[0]
    ps = permission_sets[0]
    mapping = [
        {
            "GroupId": group["GroupId"],
            "DisplayName": group["DisplayName"],
            "Description": group.get("Description"),
            "IdentityStoreId": group["IdentityStoreId"],
            "ExternalId": (
                group.get("ExternalIds", [{}])[0].get("Id")
                if group.get("ExternalIds")
                else None
            ),
            "Region": "us-west-2",
            # One-to-many assignment list
            "AssignedPermissionSets": [ps["PermissionSetArn"]],
        }
    ]

    load(
        neo4j_session,
        AWSSSOGroupSchema(),
        mapping,
        lastupdated="test_tag",
        AWS_ID=TEST_ACCOUNT_ID,
    )

    assert check_rels(
        neo4j_session,
        "AWSSSOGroup",
        "id",
        "AWSPermissionSet",
        "arn",
        "HAS_PERMISSION_SET",
        True,
    ) == {
        (
            group["GroupId"],
            ps["PermissionSetArn"],
        )
    }


def test_link_sso_user_membership_to_group(neo4j_session):
    """Test linking SSO users to SSO groups via MEMBER_OF_SSO_GROUP using standard relationships."""
    users = tests.data.aws.identitycenter.LIST_USERS
    groups = tests.data.aws.identitycenter.LIST_GROUPS

    # Load base nodes first
    transformed_users = transform_sso_users(users)
    load_sso_users(
        neo4j_session,
        transformed_users,
        "d-1234567890",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )
    load_sso_groups(
        neo4j_session,
        transform_sso_groups(groups),
        "d-1234567890",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    # Create membership mapping, enriched to avoid clobbering user properties
    user = transformed_users[0]
    group = groups[0]

    membership = [
        {
            "UserId": user["UserId"],
            "UserName": user["UserName"],
            "IdentityStoreId": user["IdentityStoreId"],
            "ExternalId": user.get("ExternalId"),
            "Region": "us-west-2",
            # One-to-many group id list
            "MemberOfGroups": [group["GroupId"]],
        }
    ]

    load(
        neo4j_session,
        AWSSSOUserSchema(),
        membership,
        lastupdated="test_tag",
        AWS_ID=TEST_ACCOUNT_ID,
    )

    assert check_rels(
        neo4j_session,
        "AWSSSOUser",
        "id",
        "AWSSSOGroup",
        "id",
        "MEMBER_OF_SSO_GROUP",
        True,
    ) == {
        (
            user["UserId"],
            group["GroupId"],
        )
    }


def test_link_sso_user_to_permission_set(neo4j_session):
    """Test linking SSO users directly to permission sets via HAS_PERMISSION_SET."""
    # Arrange
    users = tests.data.aws.identitycenter.LIST_USERS
    permission_sets = tests.data.aws.identitycenter.LIST_PERMISSION_SETS
    transformed_users = transform_sso_users(users)
    load_sso_users(
        neo4j_session,
        transformed_users,
        "d-1234567890",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )
    load_permission_sets(
        neo4j_session,
        permission_sets,
        "arn:aws:sso:::instance/ssoins-12345678901234567",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    user = transformed_users[0]
    ps = permission_sets[0]
    mapping = [
        {
            "UserId": user["UserId"],
            "UserName": user["UserName"],
            "IdentityStoreId": user["IdentityStoreId"],
            "ExternalId": user.get("ExternalId"),
            "Region": "us-west-2",
            # One-to-many assigned permission sets
            "AssignedPermissionSets": [ps["PermissionSetArn"]],
        }
    ]

    # Act
    load(
        neo4j_session,
        AWSSSOUserSchema(),
        mapping,
        lastupdated="test_tag",
        AWS_ID=TEST_ACCOUNT_ID,
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSSSOUser",
        "id",
        "AWSPermissionSet",
        "arn",
        "HAS_PERMISSION_SET",
        True,
    ) == {
        (
            user["UserId"],
            ps["PermissionSetArn"],
        )
    }


def test_group_allowed_by_role(neo4j_session):
    """Quick check that ALLOWED_BY edges from roles to groups can be created via matchlinks."""
    groups = tests.data.aws.identitycenter.LIST_GROUPS
    permission_sets = tests.data.aws.identitycenter.LIST_PERMISSION_SETS

    # Load base nodes
    load_sso_groups(
        neo4j_session,
        transform_sso_groups(groups),
        "d-1234567890",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    # Create a sample AWSRole node that we'll link to the group
    role_arn = "arn:aws:iam::1234567890:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_Test"
    neo4j_session.run(
        "MERGE (:AWSRole{arn: $arn, lastupdated: $tag})",
        arn=role_arn,
        tag="test_tag",
    )

    group = groups[0]
    ps = permission_sets[0]
    rel_data = [
        {
            "GroupId": group["GroupId"],
            "PermissionSetArn": ps["PermissionSetArn"],
            "RoleArn": role_arn,
        }
    ]

    load_role_assignments(
        neo4j_session,
        rel_data,
        TEST_ACCOUNT_ID,
        "test_tag",
        RoleAssignmentAllowedByGroupMatchLink(),
    )

    assert check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "AWSSSOGroup",
        "id",
        "ALLOWED_BY",
        True,
    ) == {
        (
            role_arn,
            group["GroupId"],
        )
    }
