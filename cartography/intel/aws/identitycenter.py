import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.aws.identitycenter.awsidentitycenter import (
    AWSIdentityCenterInstanceSchema,
)
from cartography.models.aws.identitycenter.awspermissionset import (
    AWSPermissionSetSchema,
)
from cartography.models.aws.identitycenter.awspermissionset import (
    RoleAssignmentAllowedByGroupMatchLink,
)
from cartography.models.aws.identitycenter.awspermissionset import (
    RoleAssignmentAllowedByMatchLink,
)
from cartography.models.aws.identitycenter.awssogroup import AWSSSOGroupSchema
from cartography.models.aws.identitycenter.awsssouser import AWSSSOUserSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_identity_center_instances(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
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
    instance_data: List[Dict],
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
) -> List[Dict]:
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
                permission_set["RoleHint"] = (
                    f":role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_{permission_set.get('Name')}"
                )
                permission_sets.append(permission_set)

    return permission_sets


@timeit
def load_permission_sets(
    neo4j_session: neo4j.Session,
    permission_sets: List[Dict],
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
) -> List[Dict]:
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
) -> List[Dict]:
    """
    Get all SSO groups for a given Identity Store
    """
    client = boto3_session.client("identitystore", region_name=region)
    groups: List[Dict[str, Any]] = []

    paginator = client.get_paginator("list_groups")
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        group_page = page.get("Groups", [])
        for group in group_page:
            groups.append(group)

    return groups


def transform_sso_users(
    users: List[Dict[str, Any]],
    user_group_memberships: Optional[Dict[str, List[str]]] = None,
    user_permission_sets: Optional[Dict[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Transform SSO users to match the expected schema, optionally including group memberships
    """
    transformed_users = []
    for user in users:
        if user.get("ExternalIds"):
            user["ExternalId"] = user["ExternalIds"][0].get("Id")
        # Add group memberships if provided
        if user_group_memberships:
            user["MemberOfGroups"] = user_group_memberships.get(user["UserId"], [])
        # Add direct permission set assignments if provided
        if user_permission_sets:
            user["AssignedPermissionSets"] = user_permission_sets.get(
                user["UserId"], []
            )
        transformed_users.append(user)
    return transformed_users


def transform_sso_groups(
    groups: List[Dict[str, Any]],
    group_permission_sets: Optional[Dict[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """
    Transform SSO groups to match the expected schema, optionally including permission set assignments
    """
    transformed_groups: List[Dict[str, Any]] = []
    for group in groups:
        if group.get("ExternalIds"):
            group["ExternalId"] = group["ExternalIds"][0].get("Id")
        # Add permission set assignments if provided
        if group_permission_sets:
            group["AssignedPermissionSets"] = group_permission_sets.get(
                group["GroupId"], []
            )
        transformed_groups.append(group)
    return transformed_groups


@timeit
def load_sso_users(
    neo4j_session: neo4j.Session,
    users: List[Dict],
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
    groups: List[Dict],
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
def get_role_assignments(
    boto3_session: boto3.session.Session,
    users: List[Dict],
    instance_arn: str,
    region: str,
) -> List[Dict]:
    """
    Get role assignments for SSO users
    """

    logger.info(f"Getting role assignments for {len(users)} users")
    client = boto3_session.client("sso-admin", region_name=region)
    role_assignments = []

    for user in users:
        user_id = user["UserId"]
        paginator = client.get_paginator("list_account_assignments_for_principal")
        for page in paginator.paginate(
            InstanceArn=instance_arn,
            PrincipalId=user_id,
            PrincipalType="USER",
        ):
            for assignment in page.get("AccountAssignments", []):
                role_assignments.append(
                    {
                        "UserId": user_id,
                        "PermissionSetArn": assignment.get("PermissionSetArn"),
                        "AccountId": assignment.get("AccountId"),
                    },
                )

    return role_assignments


@timeit
@aws_handle_regions
def get_group_role_assignments(
    boto3_session: boto3.session.Session,
    groups: List[Dict],
    instance_arn: str,
    region: str,
) -> List[Dict]:
    """
    Get role assignments for SSO groups
    """

    logger.info(f"Getting role assignments for {len(groups)} groups")
    client = boto3_session.client("sso-admin", region_name=region)
    role_assignments: List[Dict[str, Any]] = []

    for group in groups:
        group_id = group["GroupId"]
        paginator = client.get_paginator("list_account_assignments_for_principal")
        for page in paginator.paginate(
            InstanceArn=instance_arn,
            PrincipalId=group_id,
            PrincipalType="GROUP",
        ):
            for assignment in page.get("AccountAssignments", []):
                role_assignments.append(
                    {
                        "GroupId": group_id,
                        "PermissionSetArn": assignment.get("PermissionSetArn"),
                        "AccountId": assignment.get("AccountId"),
                    }
                )

    return role_assignments


@timeit
@aws_handle_regions
def get_user_group_memberships(
    boto3_session: boto3.session.Session,
    identity_store_id: str,
    groups: List[Dict],
    region: str,
) -> Dict[str, List[str]]:
    """
    Return a mapping of UserId -> [GroupIds] for all group memberships in the identity store.
    """
    client = boto3_session.client("identitystore", region_name=region)
    user_groups: Dict[str, List[str]] = {}

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
def get_permset_roles(
    neo4j_session: neo4j.Session,
    role_assignments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Enrich role assignments with exact role ARNs by querying existing permission set relationships.
    Uses the ASSIGNED_TO_ROLE relationships created when permission sets were loaded.
    """
    # Get unique permission set ARNs from role assignments
    permset_ids = list({ra["PermissionSetArn"] for ra in role_assignments})

    query = """
    MATCH (role:AWSRole)<-[:ASSIGNED_TO_ROLE]-(permset:AWSPermissionSet)
    WHERE permset.arn IN $PermSetIds
    RETURN permset.arn AS PermissionSetArn, role.arn AS RoleArn
    """
    result = neo4j_session.run(query, PermSetIds=permset_ids)
    permset_to_role = [record.data() for record in result]

    # Create mapping from permission set ARN to role ARN
    permset_to_role_map = {
        entry["PermissionSetArn"]: entry["RoleArn"] for entry in permset_to_role
    }

    # Enrich role assignments with exact role ARNs
    enriched_assignments = []
    for assignment in role_assignments:
        role_arn = permset_to_role_map.get(assignment["PermissionSetArn"])
        enriched_assignments.append(
            {
                **assignment,
                "RoleArn": role_arn,
            }
        )

    return enriched_assignments


@timeit
def load_role_assignments(
    neo4j_session: neo4j.Session,
    role_assignments: List[Dict],
    aws_account_id: str,
    aws_update_tag: int,
    matchlink_schema: Union[
        RoleAssignmentAllowedByMatchLink,
        RoleAssignmentAllowedByGroupMatchLink,
    ],
) -> None:
    """
    Load role assignments into the graph using the provided MatchLink schema
    """
    logger.info(f"Loading {len(role_assignments)} role assignments")
    load_matchlinks(
        neo4j_session,
        matchlink_schema,
        role_assignments,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
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
        RoleAssignmentAllowedByMatchLink(),
        "AWSAccount",
        common_job_parameters["AWS_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
    GraphJob.from_matchlink(
        RoleAssignmentAllowedByGroupMatchLink(),
        "AWSAccount",
        common_job_parameters["AWS_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)


@timeit
def sync_identity_center_instances(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync Identity Center instances, their permission sets, and SSO users
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

        # For each instance, get and load its permission sets and SSO users
        for instance in instances:
            instance_arn = instance["InstanceArn"]
            identity_store_id = instance["IdentityStoreId"]

            permission_sets = get_permission_sets(boto3_session, instance_arn, region)

            load_permission_sets(
                neo4j_session,
                permission_sets,
                instance_arn,
                region,
                current_aws_account_id,
                update_tag,
            )

            # Fetch groups first to avoid interleaving between groups and users
            groups = get_sso_groups(boto3_session, identity_store_id, region)

            # Get permission set assignments for groups
            group_permission_sets: Dict[str, List[str]] = {}
            group_role_assignments_raw = get_group_role_assignments(
                boto3_session,
                groups,
                instance_arn,
                region,
            )
            for assignment in group_role_assignments_raw:
                group_id = assignment["GroupId"]
                perm_set = assignment["PermissionSetArn"]
                group_permission_sets.setdefault(group_id, []).append(perm_set)

            # Transform and load groups with their permission set assignments FIRST
            # so that user->group membership edges can attach in the same run.
            transformed_groups = transform_sso_groups(groups, group_permission_sets)
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

            # Get direct permission set assignments for users
            user_permission_sets: Dict[str, List[str]] = {}
            user_role_assignments_raw = get_role_assignments(
                boto3_session,
                users,
                instance_arn,
                region,
            )
            for assignment in user_role_assignments_raw:
                uid = assignment["UserId"]
                perm_set = assignment["PermissionSetArn"]
                user_permission_sets.setdefault(uid, []).append(perm_set)

            # Transform and load users with their group memberships AFTER groups exist
            transformed_users = transform_sso_users(
                users,
                user_group_memberships,
                user_permission_sets,
            )
            load_sso_users(
                neo4j_session,
                transformed_users,
                identity_store_id,
                region,
                current_aws_account_id,
                update_tag,
            )

            # Enrich role assignments with exact role ARNs using permission set relationships.
            # Note: we do this after groups and users are loaded so that
            # load_role_assignments calls can MATCH existing AWSSSOUser/AWSSSOGroup
            # nodes when drawing the ALLOWED_BY edges.
            enriched_role_assignments = get_permset_roles(
                neo4j_session,
                user_role_assignments_raw,
            )
            load_role_assignments(
                neo4j_session,
                enriched_role_assignments,
                current_aws_account_id,
                update_tag,
                RoleAssignmentAllowedByMatchLink(),
            )

            enriched_group_role_assignments = get_permset_roles(
                neo4j_session,
                group_role_assignments_raw,
            )
            load_role_assignments(
                neo4j_session,
                enriched_group_role_assignments,
                current_aws_account_id,
                update_tag,
                RoleAssignmentAllowedByGroupMatchLink(),
            )

    cleanup(neo4j_session, common_job_parameters)
