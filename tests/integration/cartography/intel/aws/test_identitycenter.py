from unittest.mock import MagicMock
from unittest.mock import patch

import botocore.exceptions

import cartography.intel.aws.identitycenter
import tests.data.aws.identitycenter
from cartography.client.core.tx import load
from cartography.intel.aws.identitycenter import get_permission_sets
from cartography.intel.aws.identitycenter import load_group_roles
from cartography.intel.aws.identitycenter import load_identity_center_instances
from cartography.intel.aws.identitycenter import load_permission_sets
from cartography.intel.aws.identitycenter import load_sso_groups
from cartography.intel.aws.identitycenter import load_sso_users
from cartography.intel.aws.identitycenter import transform_permission_sets
from cartography.intel.aws.identitycenter import transform_sso_groups
from cartography.intel.aws.identitycenter import transform_sso_users
from cartography.models.aws.iam.role import AWSRoleSchema
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
        Region="us-west-2",
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
        Region="us-west-2",
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
        Region="us-west-2",
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

    load_group_roles(
        neo4j_session,
        rel_data,
        TEST_ACCOUNT_ID,
        "test_tag",
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


def test_permission_set_to_role_us_east_1(neo4j_session):
    """Test that ASSIGNED_TO_ROLE relationship is created for us-east-1 roles (without region in path)."""
    # Clear existing data
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Load mock AWS role into graph
    mock_role = tests.data.aws.identitycenter.MOCK_AWS_ROLE_US_EAST_1
    role_data = [
        {
            "arn": mock_role["Arn"],
            "name": mock_role["RoleName"],
            "roleid": mock_role["RoleId"],
            "path": mock_role["Path"],
            "createdate": str(mock_role["CreateDate"]),
            "trusted_aws_principals": [],
        }
    ]
    load(
        neo4j_session,
        AWSRoleSchema(),
        role_data,
        lastupdated="test_tag",
        AWS_ID=TEST_ACCOUNT_ID,
    )

    # Mock boto3 session and calls to get permission sets
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {
            "PermissionSets": [
                tests.data.aws.identitycenter.LIST_PERMISSION_SETS[0][
                    "PermissionSetArn"
                ]
            ]
        }
    ]
    mock_client.describe_permission_set.return_value = {
        "PermissionSet": tests.data.aws.identitycenter.LIST_PERMISSION_SETS[0]
    }

    # Call get_permission_sets with us-east-1
    permission_sets = get_permission_sets(
        mock_session,
        "arn:aws:sso:::instance/ssoins-12345678901234567",
        "us-east-1",
    )

    # Transform permission sets to add RoleHint
    permission_sets = transform_permission_sets(permission_sets, "us-east-1")

    # Verify RoleHint was generated correctly (without region)
    assert len(permission_sets) == 1
    assert (
        permission_sets[0]["RoleHint"]
        == ":role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess"
    )

    # Load permission sets - should create ASSIGNED_TO_ROLE relationship
    load_permission_sets(
        neo4j_session,
        permission_sets,
        "arn:aws:sso:::instance/ssoins-12345678901234567",
        "us-east-1",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    # Verify ASSIGNED_TO_ROLE relationship exists
    assert check_rels(
        neo4j_session,
        "AWSPermissionSet",
        "arn",
        "AWSRole",
        "arn",
        "ASSIGNED_TO_ROLE",
        True,
    ) == {
        (
            tests.data.aws.identitycenter.LIST_PERMISSION_SETS[0]["PermissionSetArn"],
            mock_role["Arn"],
        )
    }


def test_permission_set_to_role_us_west_2(neo4j_session):
    """Test that ASSIGNED_TO_ROLE relationship is created for non-us-east-1 roles (with region in path)."""
    # Clear existing data
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    # Load mock AWS role into graph
    mock_role = tests.data.aws.identitycenter.MOCK_AWS_ROLE_US_WEST_2
    role_data = [
        {
            "arn": mock_role["Arn"],
            "name": mock_role["RoleName"],
            "roleid": mock_role["RoleId"],
            "path": mock_role["Path"],
            "createdate": str(mock_role["CreateDate"]),
            "trusted_aws_principals": [],
        }
    ]
    load(
        neo4j_session,
        AWSRoleSchema(),
        role_data,
        lastupdated="test_tag",
        AWS_ID=TEST_ACCOUNT_ID,
    )

    # Mock boto3 session and calls to get permission sets
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {
            "PermissionSets": [
                tests.data.aws.identitycenter.LIST_PERMISSION_SETS[0][
                    "PermissionSetArn"
                ]
            ]
        }
    ]
    mock_client.describe_permission_set.return_value = {
        "PermissionSet": tests.data.aws.identitycenter.LIST_PERMISSION_SETS[0]
    }

    # Call get_permission_sets with us-west-2
    permission_sets = get_permission_sets(
        mock_session,
        "arn:aws:sso:::instance/ssoins-12345678901234567",
        "us-west-2",
    )

    # Transform permission sets to add RoleHint
    permission_sets = transform_permission_sets(permission_sets, "us-west-2")

    # Verify RoleHint was generated correctly (with region)
    assert len(permission_sets) == 1
    assert (
        permission_sets[0]["RoleHint"]
        == ":role/aws-reserved/sso.amazonaws.com/us-west-2/AWSReservedSSO_AdministratorAccess"
    )

    # Load permission sets - should create ASSIGNED_TO_ROLE relationship
    load_permission_sets(
        neo4j_session,
        permission_sets,
        "arn:aws:sso:::instance/ssoins-12345678901234567",
        "us-west-2",
        TEST_ACCOUNT_ID,
        "test_tag",
    )

    # Verify ASSIGNED_TO_ROLE relationship exists
    assert check_rels(
        neo4j_session,
        "AWSPermissionSet",
        "arn",
        "AWSRole",
        "arn",
        "ASSIGNED_TO_ROLE",
        True,
    ) == {
        (
            tests.data.aws.identitycenter.LIST_PERMISSION_SETS[0]["PermissionSetArn"],
            mock_role["Arn"],
        )
    }


@patch.object(
    cartography.intel.aws.identitycenter,
    "get_permission_sets",
    side_effect=botocore.exceptions.ClientError(
        error_response={
            "Error": {
                "Code": "ValidationException",
                "Message": "The operation is not supported for this Identity Center instance",
            }
        },
        operation_name="ListPermissionSets",
    ),
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_identity_center_instances",
    return_value=[
        {
            "InstanceArn": "arn:aws:sso:::instance/ssoins-test",
            "IdentityStoreId": "d-test123",
        }
    ],
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_sso_users",
    return_value=tests.data.aws.identitycenter.LIST_USERS,
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_sso_groups",
    return_value=tests.data.aws.identitycenter.LIST_GROUPS,
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_user_group_memberships",
    return_value={},
)
def test_sync_account_instance_skips_permission_sets(
    mock_memberships,
    mock_groups,
    mock_users,
    mock_instances,
    mock_permission_sets,
    neo4j_session,
):
    """
    Test that account-scoped Identity Center instances gracefully skip permission set sync.

    Account-scoped Identity Center instances don't support permission sets and return a
    ValidationException when ListPermissionSets is called. This test verifies that:
    1. Users and groups ARE synced successfully
    2. Permission sets are NOT synced (no nodes created)
    3. The sync doesn't crash
    """
    # Act - Call the sync function
    cartography.intel.aws.identitycenter.sync_identity_center_instances(
        neo4j_session,
        boto3_session=None,  # Mocked via patches
        regions=["us-east-1"],
        current_aws_account_id=TEST_ACCOUNT_ID,
        update_tag=123,
        common_job_parameters={"AWS_ID": TEST_ACCOUNT_ID, "UPDATE_TAG": 123},
    )

    # Assert OUTCOME 1: Users ARE synced
    expected_users = {
        (user["UserId"],) for user in tests.data.aws.identitycenter.LIST_USERS
    }
    assert check_nodes(neo4j_session, "AWSSSOUser", ["id"]) == expected_users

    # Assert OUTCOME 2: Groups ARE synced
    expected_groups = {
        (group["GroupId"],) for group in tests.data.aws.identitycenter.LIST_GROUPS
    }
    assert check_nodes(neo4j_session, "AWSSSOGroup", ["id"]) == expected_groups

    # Assert OUTCOME 3: Permission sets are NOT synced for our test instance
    # Query for permission sets belonging to our test instance
    query = """
    MATCH (i:AWSIdentityCenter {id: $instance_arn})-[:RESOURCE]->(ps:AWSPermissionSet)
    RETURN ps.id as id
    """
    result = neo4j_session.run(query, instance_arn="arn:aws:sso:::instance/ssoins-test")
    permission_sets_for_test_instance = {(record["id"],) for record in result}
    assert (
        permission_sets_for_test_instance == set()
    ), f"Expected no permission sets for test instance, but found: {permission_sets_for_test_instance}"

    # Assert OUTCOME 4: Our test instance is synced
    all_instances = check_nodes(neo4j_session, "AWSIdentityCenter", ["id"])
    assert (
        "arn:aws:sso:::instance/ssoins-test",
    ) in all_instances, f"Expected test instance to be synced, but it wasn't found. Instances: {all_instances}"

    # Assert OUTCOME 5: No ALLOWED_BY relationships are created without permission sets
    assert (
        check_rels(
            neo4j_session,
            "AWSRole",
            "arn",
            "AWSSSOUser",
            "id",
            "ALLOWED_BY",
            True,
        )
        == set()
    )

    assert (
        check_rels(
            neo4j_session,
            "AWSRole",
            "arn",
            "AWSSSOGroup",
            "id",
            "ALLOWED_BY",
            True,
        )
        == set()
    )


@patch.object(
    cartography.intel.aws.identitycenter,
    "get_user_group_memberships",
    return_value={},
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_group_permissionsets",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_user_permissionsets",
    return_value=tests.data.aws.identitycenter.MULTI_ACCOUNT_USER_ASSIGNMENTS,
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_sso_groups",
    return_value=tests.data.aws.identitycenter.LIST_GROUPS,
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_sso_users",
    return_value=tests.data.aws.identitycenter.LIST_USERS,
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_permission_sets",
    return_value=tests.data.aws.identitycenter.LIST_PERMISSION_SETS,
)
@patch.object(
    cartography.intel.aws.identitycenter,
    "get_identity_center_instances",
    return_value=tests.data.aws.identitycenter.LIST_INSTANCES,
)
def test_multi_account_permission_set_assignments(
    mock_instances,
    mock_permission_sets,
    mock_users,
    mock_groups,
    mock_user_permissionsets,
    mock_group_permissionsets,
    mock_memberships,
    neo4j_session,
):
    """
    Test that user assignments to permission sets are correctly scoped to specific accounts.

    This test proves the fix for the multi-account false positive bug where users assigned to
    a permission set on 2 out of 3 accounts were incorrectly showing ALLOWED_BY relationships
    to all 3 accounts.

    Scenario:
    - 3 AWS accounts exist (pre-populated from IAM sync)
    - A permission set is provisioned to all 3 accounts (creating 3 IAM roles from IAM sync)
    - A user is assigned to the permission set on ONLY accounts 1 and 2
    - sync_identity_center_instances() runs and creates relationships

    Expected outcome:
    - User has ALLOWED_BY relationships to roles in accounts 1 and 2 ONLY
    - User does NOT have ALLOWED_BY relationship to role in account 3
    """
    # Arrange - Pre-populate AWS accounts (simulating they were created by AWS account sync)
    for account_id in tests.data.aws.identitycenter.MULTI_ACCOUNT_TEST_ACCOUNTS:
        neo4j_session.run(
            "MERGE (a:AWSAccount {id: $account_id}) SET a.lastupdated = $update_tag",
            account_id=account_id,
            update_tag=123,
        )

    # Arrange - Pre-populate IAM roles (simulating they were created by AWS IAM sync)
    # These roles exist in all 3 accounts for the same permission set
    role_data = [
        {
            "arn": role["Arn"],
            "name": role["RoleName"],
            "roleid": role["RoleId"],
            "path": role["Path"],
            "createdate": str(role["CreateDate"]),
            "trusted_aws_principals": [],
        }
        for role in tests.data.aws.identitycenter.MULTI_ACCOUNT_TEST_ROLES
    ]

    for i, role in enumerate(role_data):
        load(
            neo4j_session,
            AWSRoleSchema(),
            [role],
            lastupdated=123,
            AWS_ID=tests.data.aws.identitycenter.MULTI_ACCOUNT_TEST_ACCOUNTS[i],
        )

    # Act - Run the complete sync flow
    cartography.intel.aws.identitycenter.sync_identity_center_instances(
        neo4j_session,
        boto3_session=None,  # Mocked via patches
        regions=["us-east-1"],
        current_aws_account_id=TEST_ACCOUNT_ID,
        update_tag=123,
        common_job_parameters={"AWS_ID": TEST_ACCOUNT_ID, "UPDATE_TAG": 123},
    )

    # Assert - User has ALLOWED_BY to roles in accounts 1 and 2 ONLY
    user_id = tests.data.aws.identitycenter.LIST_USERS[0]["UserId"]
    role_arns_with_allowed_by = neo4j_session.run(
        """
        MATCH (user:AWSSSOUser {id: $user_id})<-[:ALLOWED_BY]-(role:AWSRole)
        RETURN role.arn as role_arn
        """,
        user_id=user_id,
    )
    actual_role_arns = {record["role_arn"] for record in role_arns_with_allowed_by}

    expected_role_arns = {
        tests.data.aws.identitycenter.MULTI_ACCOUNT_TEST_ROLES[0]["Arn"],  # Account 1
        tests.data.aws.identitycenter.MULTI_ACCOUNT_TEST_ROLES[1]["Arn"],  # Account 2
        # NOT Account 3
    }

    assert actual_role_arns == expected_role_arns, (
        f"Expected user to have ALLOWED_BY relationships to roles in accounts 1 and 2 only. "
        f"Expected: {expected_role_arns}, Actual: {actual_role_arns}"
    )

    # Additional verification - Ensure role in account 3 exists but has NO ALLOWED_BY to user
    role_3_arn = tests.data.aws.identitycenter.MULTI_ACCOUNT_TEST_ROLES[2]["Arn"]
    assert role_3_arn not in actual_role_arns, (
        f"User should NOT have ALLOWED_BY relationship to role in account 3 ({role_3_arn}), "
        f"but it was found in: {actual_role_arns}"
    )

    # Verify account 3 role exists in the graph (sanity check)
    role_3_exists = neo4j_session.run(
        "MATCH (role:AWSRole {arn: $arn}) RETURN count(role) as count",
        arn=role_3_arn,
    ).single()["count"]
    assert (
        role_3_exists == 1
    ), f"Role in account 3 should exist in graph but was not found: {role_3_arn}"
