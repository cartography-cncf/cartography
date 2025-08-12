import logging
from typing import Any
from typing import Dict
from typing import List

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
    RoleAssignmentAllowedByMatchLink,
)
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


def transform_sso_users(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform SSO users to match the expected schema
    """
    transformed_users = []
    for user in users:
        if user.get("ExternalIds") is not None:
            user["ExternalId"] = user["ExternalIds"][0].get("Id")
        transformed_users.append(user)
    return transformed_users


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
) -> None:
    """
    Load role assignments into the graph using MatchLink schema
    """
    logger.info(f"Loading {len(role_assignments)} role assignments")
    load_matchlinks(
        neo4j_session,
        RoleAssignmentAllowedByMatchLink(),
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

    # Clean up role assignment MatchLinks
    GraphJob.from_matchlink(
        RoleAssignmentAllowedByMatchLink(),
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

            users = get_sso_users(boto3_session, identity_store_id, region)
            transformed_users = transform_sso_users(users)
            load_sso_users(
                neo4j_session,
                transformed_users,
                identity_store_id,
                region,
                current_aws_account_id,
                update_tag,
            )

            # Get and load role assignments
            role_assignments = get_role_assignments(
                boto3_session,
                users,
                instance_arn,
                region,
            )

            # Enrich role assignments with exact role ARNs using permission set relationships
            enriched_role_assignments = get_permset_roles(
                neo4j_session,
                role_assignments,
            )
            load_role_assignments(
                neo4j_session,
                enriched_role_assignments,
                current_aws_account_id,
                update_tag,
            )

    cleanup(neo4j_session, common_job_parameters)
