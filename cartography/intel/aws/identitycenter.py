import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.identitycenter.awsidentitycenter import AWSIdentityCenterInstanceSchema
from cartography.models.aws.identitycenter.awspermissionset import AWSPermissionSetSchema
from cartography.models.aws.identitycenter.awsssouser import AWSSSOUserSchema
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit
logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_identity_center_instances(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Get all AWS IAM Identity Center instances in the current region
    """
    client = boto3_session.client('sso-admin', region_name=region)
    instances = []

    paginator = client.get_paginator('list_instances')
    for page in paginator.paginate():
        instances.extend(page.get('Instances', []))

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
    logger.info(f"Loading {len(instance_data)} Identity Center instances for region {region}")
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
def get_permission_sets(boto3_session: boto3.session.Session, instance_arn: str, region: str) -> List[Dict]:
    """
    Get all permission sets for a given Identity Center instance
    """
    client = boto3_session.client('sso-admin', region_name=region)
    permission_sets = []

    paginator = client.get_paginator('list_permission_sets')
    for page in paginator.paginate(InstanceArn=instance_arn):
        # Get detailed info for each permission set
        for arn in page.get('PermissionSets', []):
            details = client.describe_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=arn,
            )
            permission_set = details.get('PermissionSet', {})
            if permission_set:
                permission_set['RoleHint'] = (
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
    logger.info(f"Loading {len(permission_sets)} permission sets for instance {instance_arn} in region {region}")

    load(
        neo4j_session,
        AWSPermissionSetSchema(),
        permission_sets,
        lastupdated=aws_update_tag,
        InstanceArn=instance_arn,
        Region=region,
        AWS_ID=aws_account_id,
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
    client = boto3_session.client('identitystore', region_name=region)
    users = []

    paginator = client.get_paginator('list_users')
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        user_page = page.get('Users', [])
        for user in user_page:
            if user.get('ExternalIds', None):
                user['ExternalId'] = user.get('ExternalIds')[0].get('Id')
            users.append(user)

    return users


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
    logger.info(f"Loading {len(users)} SSO users for identity store {identity_store_id} in region {region}")

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
    client = boto3_session.client('sso-admin', region_name=region)
    role_assignments = []

    for user in users:
        user_id = user['UserId']
        paginator = client.get_paginator('list_account_assignments_for_principal')
        for page in paginator.paginate(InstanceArn=instance_arn, PrincipalId=user_id, PrincipalType='USER'):
            for assignment in page.get('AccountAssignments', []):
                role_assignments.append({
                    'UserId': user_id,
                    'PermissionSetArn': assignment.get('PermissionSetArn'),
                    'AccountId': assignment.get('AccountId'),
                })

    return role_assignments


@timeit
def load_role_assignments(
    neo4j_session: neo4j.Session,
    role_assignments: List[Dict],
    aws_update_tag: int,
) -> None:
    """
    Load role assignments into the graph
    """
    logger.info(f"Loading {len(role_assignments)} role assignments")
    if role_assignments:
        neo4j_session.run(
            """
            UNWIND $role_assignments AS ra
            MATCH (acc:AWSAccount{id:ra.AccountId}) -[:RESOURCE]->
            (role:AWSRole)<-[:ASSIGNED_TO_ROLE]-
            (permset:AWSPermissionSet {id: ra.PermissionSetArn})
            MATCH (sso:AWSSSOUser {id: ra.UserId})
            MERGE (role)-[r:ALLOWED_BY]->(sso)
            SET r.lastupdated = $aws_update_tag,
            r.permission_set_arn = ra.PermissionSetArn
            """,
            role_assignments=role_assignments,
            aws_update_tag=aws_update_tag,
        )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(AWSIdentityCenterInstanceSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(AWSPermissionSetSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(AWSSSOUserSchema(), common_job_parameters).run(neo4j_session)
    run_cleanup_job(
        'aws_import_identity_center_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


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
            instance_arn = instance['InstanceArn']
            identity_store_id = instance['IdentityStoreId']

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
            load_sso_users(
                neo4j_session,
                users,
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
            load_role_assignments(
                neo4j_session,
                role_assignments,
                update_tag,
            )

    cleanup(neo4j_session, common_job_parameters)
