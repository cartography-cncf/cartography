import logging
from typing import Any

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.models.aws.identitycenter.awsidentitycenter import (
    AWSIdentityCenterInstanceSchema,
)
from cartography.models.aws.identitycenter.awspermissionset import (
    AWSPermissionSetSchema,
)
from cartography.models.aws.identitycenter.awspermissionset import (
    AWSRoleToSSOGroupMatchLink,
)
from cartography.models.aws.identitycenter.awspermissionset import (
    AWSRoleToSSOUserMatchLink,
)
from cartography.models.aws.identitycenter.awssogroup import AWSSSOGroupSchema
from cartography.models.aws.identitycenter.awsssouser import AWSSSOUserSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _is_permission_set_sync_unsupported_error(
    error: botocore.exceptions.ClientError,
) -> bool:
    """Return True when the Identity Center instance does not support permission sets."""
    error_info = error.response.get("Error", {})
    if error_info.get("Code") != "ValidationException":
        return False

    message = error_info.get("Message", "").lower()
    return "not supported for this identity center instance" in message


@timeit
@aws_handle_regions
def get_identity_center_instances(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all AWS IAM Identity Center instances in the current region
    """
    client = boto3_session.client("sso-admin", region_name=region)
    instances = []

    paginator = client.get_paginator("list_instances")
    for page in paginator.paginate():
        instances.extend(page.get("Instances", []))

    return instances


@timeit
def load_identity_center_instances(
    neo4j_session: neo4j.Session,
    instance_data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load Identity Center instances into the graph
    """
    logger.info(
        f"Loading {len(instance_data)} Identity Center instances for region {region}",
    )
    load(
        neo4j_session,
        AWSIdentityCenterInstanceSchema(),
        instance_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
@aws_handle_regions
def get_permission_sets(
    boto3_session: boto3.session.Session,
    instance_arn: str,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all permission sets for a given Identity Center instance
    """
    client = boto3_session.client("sso-admin", region_name=region)
    permission_sets = []

    paginator = client.get_paginator("list_permission_sets")
    for page in paginator.paginate(InstanceArn=instance_arn):
        # Get detailed info for each permission set
        for arn in page.get("PermissionSets", []):
            details = client.describe_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=arn,
            )
            permission_set = details.get("PermissionSet", {})
            if permission_set:
                permission_sets.append(permission_set)

    return permission_sets


def transform_permission_sets(
    permission_sets: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform permission sets by adding the RoleHint based on region.

    AWS SSO roles in us-east-1 don't include region in the ARN path,
    but roles in other regions do: /aws-reserved/sso.amazonaws.com/{region}/AWSReservedSSO_*
    """
    for permission_set in permission_sets:
        if region == "us-east-1":
            permission_set["RoleHint"] = (
                f":role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_{permission_set.get('Name')}"
            )
        else:
            permission_set["RoleHint"] = (
                f":role/aws-reserved/sso.amazonaws.com/{region}/AWSReservedSSO_{permission_set.get('Name')}"
            )
    return permission_sets


@timeit
def load_permission_sets(
    neo4j_session: neo4j.Session,
    permission_sets: list[dict[str, Any]],
    instance_arn: str,
    region: str,
    aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load Identity Center permission sets into the graph
    """
    logger.info(
        f"Loading {len(permission_sets)} permission sets for instance {instance_arn} in region {region}",
    )

    load(
        neo4j_session,
        AWSPermissionSetSchema(),
        permission_sets,
        lastupdated=aws_update_tag,
        InstanceArn=instance_arn,
        Region=region,
        AWS_ID=aws_account_id,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=aws_account_id,
    )


@timeit
@aws_handle_regions
def get_sso_users(
    boto3_session: boto3.session.Session,
    identity_store_id: str,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SSO users for a given Identity Store
    """
    client = boto3_session.client("identitystore", region_name=region)
    users = []

    paginator = client.get_paginator("list_users")
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        user_page = page.get("Users", [])
        for user in user_page:
            users.append(user)

    return users


@timeit
@aws_handle_regions
def get_sso_groups(
    boto3_session: boto3.session.Session,
    identity_store_id: str,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SSO groups for a given Identity Store
    """
    client = boto3_session.client("identitystore", region_name=region)
    groups: list[dict[str, Any]] = []

    paginator = client.get_paginator("list_groups")
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        group_page = page.get("Groups", [])
        for group in group_page:
            groups.append(group)

    return groups


def transform_sso_users(
    users: list[dict[str, Any]],
    user_group_memberships: dict[str, list[str]] | None = None,
    user_permissionsets: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Transform SSO users to match the expected schema, optionally including group memberships
    and permission set assignments.

    Args:
        users: List of SSO users from AWS API
        user_group_memberships: Optional mapping of UserId -> [GroupIds]
        user_permissionsets: Optional list of permission set assignments with shape:
            [{UserId: str, PermissionSetArn: str, AccountId: str}, ...]

    Returns:
        Transformed users with MemberOfGroups and AssignedPermissionSets fields added
    """
    # Build mapping from UserId to list of PermissionSetArns
    user_permission_sets: dict[str, list[str]] = {}
    if user_permissionsets:
        for assignment in user_permissionsets:
            user_id = assignment["UserId"]
            perm_set = assignment["PermissionSetArn"]
            user_permission_sets.setdefault(user_id, []).append(perm_set)

    # Transform users
    transformed_users = []
    for user in users:
        if user.get("ExternalIds"):
            user["ExternalId"] = user["ExternalIds"][0].get("Id")
        # Add group memberships if provided
        if user_group_memberships:
            user["MemberOfGroups"] = user_group_memberships.get(user["UserId"], [])
        # Add direct permission set assignments if available
        if user_permission_sets:
            user["AssignedPermissionSets"] = user_permission_sets.get(
                user["UserId"], []
            )
        transformed_users.append(user)
    return transformed_users


def transform_sso_groups(
    groups: list[dict[str, Any]],
    group_role_assignments: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Transform SSO groups to match the expected schema, optionally including permission set assignments.

    Args:
        groups: List of SSO groups from AWS API
        group_role_assignments: Optional list of role assignments with shape:
            [{GroupId: str, PermissionSetArn: str, AccountId: str}, ...]

    Returns:
        Transformed groups with AssignedPermissionSets field added
    """
    # Build mapping from GroupId to list of PermissionSetArns
    group_permission_sets: dict[str, list[str]] = {}
    if group_role_assignments:
        for assignment in group_role_assignments:
            group_id = assignment["GroupId"]
            perm_set = assignment["PermissionSetArn"]
            group_permission_sets.setdefault(group_id, []).append(perm_set)

    # Transform groups
    transformed_groups: list[dict[str, Any]] = []
    for group in groups:
        if group.get("ExternalIds"):
            group["ExternalId"] = group["ExternalIds"][0].get("Id")
        # Add permission set assignments if available
        if group_permission_sets:
            group["AssignedPermissionSets"] = group_permission_sets.get(
                group["GroupId"], []
            )
        transformed_groups.append(group)
    return transformed_groups


@timeit
def load_sso_users(
    neo4j_session: neo4j.Session,
    users: list[dict[str, Any]],
    identity_store_id: str,
    region: str,
    aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load SSO users into the graph
    """
    logger.info(
        f"Loading {len(users)} SSO users for identity store {identity_store_id} in region {region}",
    )

    load(
        neo4j_session,
        AWSSSOUserSchema(),
        users,
        lastupdated=aws_update_tag,
        IdentityStoreId=identity_store_id,
        AWS_ID=aws_account_id,
        Region=region,
    )


@timeit
def load_sso_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict[str, Any]],
    identity_store_id: str,
    region: str,
    aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load SSO groups into the graph
    """
    logger.info(
        f"Loading {len(groups)} SSO groups for identity store {identity_store_id} in region {region}",
    )

    load(
        neo4j_session,
        AWSSSOGroupSchema(),
        groups,
        lastupdated=aws_update_tag,
        IdentityStoreId=identity_store_id,
        AWS_ID=aws_account_id,
        Region=region,
    )


@timeit
@aws_handle_regions
def get_user_permissionsets(
    boto3_session: boto3.session.Session,
    users: list[dict[str, Any]],
    instance_arn: str,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get permissionsets for SSO users, taking into account which accounts the user is assigned to.
    Although a permissionset can be assigned to multiple accounts, it is possible for the user
    to be assigned to just a subset of those!
    """
    logger.info(f"Getting permissionsets for {len(users)} users")
    client = boto3_session.client("sso-admin", region_name=region)
    user_permissionsets = []

    for user in users:
        user_id = user["UserId"]
        paginator = client.get_paginator("list_account_assignments_for_principal")
        for page in paginator.paginate(
            InstanceArn=instance_arn,
            PrincipalId=user_id,
            PrincipalType="USER",
        ):
            for assignment in page.get("AccountAssignments", []):
                user_permissionsets.append(
                    {
                        "UserId": user_id,
                        "PermissionSetArn": assignment.get("PermissionSetArn"),
                        "AccountId": assignment.get("AccountId"),
                    },
                )

    return user_permissionsets


@timeit
@aws_handle_regions
def get_group_permissionsets(
    boto3_session: boto3.session.Session,
    groups: list[dict[str, Any]],
    instance_arn: str,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get permissionsets for SSO groups, taking into account which accounts the group is assigned to.
    """
    logger.info(f"Getting permissionsets for {len(groups)} groups")
    client = boto3_session.client("sso-admin", region_name=region)
    group_permissionsets: list[dict[str, Any]] = []

    for group in groups:
        group_id = group["GroupId"]
        paginator = client.get_paginator("list_account_assignments_for_principal")
        for page in paginator.paginate(
            InstanceArn=instance_arn,
            PrincipalId=group_id,
            PrincipalType="GROUP",
        ):
            for assignment in page.get("AccountAssignments", []):
                group_permissionsets.append(
                    {
                        "GroupId": group_id,
                        "PermissionSetArn": assignment.get("PermissionSetArn"),
                        "AccountId": assignment.get("AccountId"),
                    }
                )

    return group_permissionsets


@timeit
@aws_handle_regions
def get_user_group_memberships(
    boto3_session: boto3.session.Session,
    identity_store_id: str,
    groups: list[dict[str, Any]],
    region: str,
) -> dict[str, list[str]]:
    """
    Return a mapping of UserId -> [GroupIds] for all group memberships in the identity store.
    """
    client = boto3_session.client("identitystore", region_name=region)
    user_groups: dict[str, list[str]] = {}

    for group in groups:
        group_id = group["GroupId"]
        paginator = client.get_paginator("list_group_memberships")
        for page in paginator.paginate(
            IdentityStoreId=identity_store_id, GroupId=group_id
        ):
            for membership in page.get("GroupMemberships", []):
                member = membership.get("MemberId", {})
                user_id = member.get("UserId")
                if user_id:
                    user_groups.setdefault(user_id, []).append(group_id)

    return user_groups


@timeit
def _get_permset_roles(
    neo4j_session: neo4j.Session,
    permset_ids: list[str],
) -> dict[tuple[str, str], str]:
    """
    Given a list of permission set ARNs, return a mapping of (permission set ARN, account ID) to role ARN
    based on the ASSIGNED_TO_ROLE relationship in the graph.
    """
    query = """
    MATCH (role:AWSRole)<-[:ASSIGNED_TO_ROLE]-(permset:AWSPermissionSet)
    MATCH (account:AWSAccount)-[:RESOURCE]->(role)
    WHERE permset.arn IN $PermSetIds
    RETURN permset.arn AS PermissionSetArn, role.arn AS RoleArn, account.id AS AccountId
    """
    permset_to_role = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        PermSetIds=permset_ids,
    )
    return {
        (entry["PermissionSetArn"], entry["AccountId"]): entry["RoleArn"]
        for entry in permset_to_role
    }


@timeit
def get_principal_roles(
    neo4j_session: neo4j.Session,
    principal_assignments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    At this point we've established that the principal has access to a given account
    via a given permission set, and now we need to find the exact role in the account
    it has access to.
    :param neo4j_session: neo4j.Session
    :param principal_assignments: either a list of {
                "UserId": str
                "AccountId": str,
                "PermissionSetArn": str,
            }, or a list of {
                "GroupId": str,
                "AccountId": str,
                "PermissionSetArn": str,
            }
    :return: either a list of {
        "UserId": str,
        "AccountId": str,
        "PermissionSetArn": str,
        "RoleArn": str
    } or,
    a list of  {
        "GroupId": str,
        "AccountId": str,
        "PermissionSetArn": str,
        "RoleArn": str
    }
    """
    # Get unique permission set ARNs from role assignments
    permset_ids = list({pa["PermissionSetArn"] for pa in principal_assignments})
    permset_to_role = _get_permset_roles(neo4j_session, permset_ids)

    unmatched = 0
    # Use the lookup table to enrich assignments with exact role ARNs
    principal_roles = []
    for assignment in principal_assignments:
        lookup_key = (assignment["PermissionSetArn"], assignment["AccountId"])
        role_arn = permset_to_role.get(lookup_key)
        if not role_arn:
            unmatched += 1
        principal_roles.append(
            {
                **assignment,
                "RoleArn": role_arn,
            }
        )
    if unmatched > 0:
        logger.info(
            f"Identity Center: {unmatched} of {len(principal_assignments)} principal assignments "
            "did not match a role. This usually means IAM roles for some permission sets/accounts "
            "have not been ingested yet. Re-run the IAM sync, and then the Identity Center sync to fix."
        )
    return principal_roles


@timeit
def load_user_roles(
    neo4j_session: neo4j.Session,
    user_roles: list[dict[str, Any]],
    aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(f"Loading {len(user_roles)} user roles")
    load_matchlinks(
        neo4j_session,
        AWSRoleToSSOUserMatchLink(),
        user_roles,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=aws_account_id,
    )


@timeit
def load_group_roles(
    neo4j_session: neo4j.Session,
    group_roles: list[dict[str, Any]],
    aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(f"Loading {len(group_roles)} group roles")
    load_matchlinks(
        neo4j_session,
        AWSRoleToSSOGroupMatchLink(),
        group_roles,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        AWSIdentityCenterInstanceSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(AWSPermissionSetSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(AWSSSOUserSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(AWSSSOGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )

    # Clean up role assignment MatchLinks
    GraphJob.from_matchlink(
        AWSRoleToSSOUserMatchLink(),
        "AWSAccount",
        common_job_parameters["AWS_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        AWSRoleToSSOGroupMatchLink(),
        "AWSAccount",
        common_job_parameters["AWS_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)


def _sync_permission_sets(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    instance_arn: str,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> bool:
    """
    Sync permission sets for an Identity Center instance.

    Returns:
        True if permission set sync is supported, False for account-scoped instances
        that don't support permission sets.
    """
    try:
        permission_sets = get_permission_sets(boto3_session, instance_arn, region)
        # Transform permission sets to add RoleHint for fuzzy matching to IAM roles
        permission_sets = transform_permission_sets(permission_sets, region)
        load_permission_sets(
            neo4j_session,
            permission_sets,
            instance_arn,
            region,
            current_aws_account_id,
            update_tag,
        )
        return True
    except botocore.exceptions.ClientError as error:
        if _is_permission_set_sync_unsupported_error(error):
            logger.warning(
                "Skipping permission set sync for Identity Center instance %s in region %s "
                "because the instance does not support permission sets. "
                "Will attempt to sync users and groups only.",
                instance_arn,
                region,
            )
            return False
        raise


def _sync_groups_and_users(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    instance_arn: str,
    identity_store_id: str,
    region: str,
    permission_set_sync_supported: bool,
    current_aws_account_id: str,
    update_tag: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Sync groups and users for an Identity Center instance.

    Groups are synced first so that user->group membership edges can be created.
    Permission set assignments are fetched (if supported) and used to enrich
    the user/group nodes with HAS_PERMISSION_SET relationships, then returned
    for later role assignment creation.

    Args:
        permission_set_sync_supported: If True, fetches and enriches permission set assignments

    Returns:
        (user_permission_set_assignments, group_permission_set_assignments)
        These are the raw assignment data needed for creating ALLOWED_BY relationships.
        Will be empty lists if permission_set_sync_supported is False.
    """
    # Fetch groups first to avoid interleaving between groups and users
    groups = get_sso_groups(boto3_session, identity_store_id, region)

    # Get permission set assignments for groups (if permission sets are supported)
    group_permissionsets_raw: list[dict[str, Any]] = []
    if permission_set_sync_supported:
        group_permissionsets_raw = get_group_permissionsets(
            boto3_session,
            groups,
            instance_arn,
            region,
        )

    # Transform and load groups with their permission set assignments FIRST
    # so that user->group membership edges can attach in the same run.
    transformed_groups = transform_sso_groups(groups, group_permissionsets_raw)
    load_sso_groups(
        neo4j_session,
        transformed_groups,
        identity_store_id,
        region,
        current_aws_account_id,
        update_tag,
    )

    # Handle users AFTER groups exist
    users = get_sso_users(boto3_session, identity_store_id, region)
    user_group_memberships = get_user_group_memberships(
        boto3_session,
        identity_store_id,
        groups,
        region,
    )

    # Get direct permission set assignments for users (if permission sets are supported)
    user_permissionsets_raw: list[dict[str, Any]] = []
    if permission_set_sync_supported:
        user_permissionsets_raw = get_user_permissionsets(
            boto3_session,
            users,
            instance_arn,
            region,
        )

    # Transform and load users with their group memberships AFTER groups exist
    transformed_users = transform_sso_users(
        users,
        user_group_memberships,
        user_permissionsets_raw,
    )
    load_sso_users(
        neo4j_session,
        transformed_users,
        identity_store_id,
        region,
        current_aws_account_id,
        update_tag,
    )

    # Return the raw assignment data for role assignment creation
    return user_permissionsets_raw, group_permissionsets_raw


def _sync_role_assignments(
    neo4j_session: neo4j.Session,
    user_permissionsets_raw: list[dict[str, Any]],
    group_permissionsets_raw: list[dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Create ALLOWED_BY relationships between IAM roles and SSO principals.

    This enriches the raw permission set assignment data with exact role ARNs
    from the graph (using the composite key lookup), then creates the MatchLink
    relationships.

    Note: This must be called AFTER groups and users are loaded so that the
    MatchLinks can find the existing AWSSSOUser/AWSSSOGroup nodes when creating
    the ALLOWED_BY edges.
    """
    user_roles = get_principal_roles(neo4j_session, user_permissionsets_raw)
    load_user_roles(neo4j_session, user_roles, current_aws_account_id, update_tag)

    group_roles = get_principal_roles(neo4j_session, group_permissionsets_raw)
    load_group_roles(neo4j_session, group_roles, current_aws_account_id, update_tag)


def _sync_instance(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    instance: dict[str, Any],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Sync a single Identity Center instance.

    This syncs permission sets (if supported), groups, users, and role assignments
    in the correct order to ensure all relationships can be created.
    """
    instance_arn = instance["InstanceArn"]
    identity_store_id = instance["IdentityStoreId"]

    # Sync permission sets (may not be supported for account-scoped instances)
    permission_set_sync_supported = _sync_permission_sets(
        neo4j_session,
        boto3_session,
        instance_arn,
        region,
        current_aws_account_id,
        update_tag,
    )

    # Sync groups and users (always happens, but enriched with permission sets if available)
    user_assignments, group_assignments = _sync_groups_and_users(
        neo4j_session,
        boto3_session,
        instance_arn,
        identity_store_id,
        region,
        permission_set_sync_supported,
        current_aws_account_id,
        update_tag,
    )

    # Create role assignment relationships (only if permission sets are supported)
    if permission_set_sync_supported:
        _sync_role_assignments(
            neo4j_session,
            user_assignments,
            group_assignments,
            current_aws_account_id,
            update_tag,
        )


@timeit
def sync_identity_center_instances(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Identity Center instances across all specified regions.

    For each instance, syncs:
    1. Permission sets (if supported by the instance type)
    2. Groups and users (with permission set assignments if available)
    3. Role assignment relationships (ALLOWED_BY edges from roles to principals)

    Account-scoped Identity Center instances don't support permission sets and will
    skip step 1 and 3, but still sync users and groups.
    """
    logger.info(f"Syncing Identity Center instances for regions {regions}")
    for region in regions:
        logger.info(f"Syncing Identity Center instances for region {region}")
        instances = get_identity_center_instances(boto3_session, region)
        load_identity_center_instances(
            neo4j_session,
            instances,
            region,
            current_aws_account_id,
            update_tag,
        )

        for instance in instances:
            _sync_instance(
                neo4j_session,
                boto3_session,
                instance,
                region,
                current_aws_account_id,
                update_tag,
            )

    cleanup(neo4j_session, common_job_parameters)
