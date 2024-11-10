import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.models.aws.identitycenter.identitycenter import IdentityCenterInstanceSchema
from cartography.models.aws.identitycenter.permissionsets import PermissionSetSchema
from cartography.models.aws.identitycenter.ssouser import SSOUserSchema
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

    try:
        paginator = client.get_paginator('list_instances')
        for page in paginator.paginate():
            instances.extend(page.get('Instances', []))
    except client.exceptions.ClientError as e:
        logger.warning(f"Failed to get Identity Center instances in region {region}: {e}")
        return []

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
        IdentityCenterInstanceSchema(),
        instance_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_identity_center_instances(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale Identity Center instance nodes and relationships
    """
    run_cleanup_job(
        'aws_import_identity_center_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def get_permission_sets(boto3_session: boto3.session.Session, instance_arn: str, region: str) -> List[Dict]:
    """
    Get all permission sets for a given Identity Center instance
    """
    client = boto3_session.client('sso-admin', region_name=region)
    permission_sets = []

    try:
        paginator = client.get_paginator('list_permission_sets')
        for page in paginator.paginate(InstanceArn=instance_arn):
            # Get detailed info for each permission set
            for arn in page.get('PermissionSets', []):
                try:
                    details = client.describe_permission_set(
                        InstanceArn=instance_arn,
                        PermissionSetArn=arn,
                    )
                    permission_sets.append(details.get('PermissionSet', {}))
                except client.exceptions.ClientError as e:
                    logger.warning(f"Failed to get details for permission set {arn}: {e}")
    except client.exceptions.ClientError as e:
        logger.warning(f"Failed to get permission sets for instance {instance_arn} in region {region}: {e}")
        return []

    return permission_sets


@timeit
def get_permission_set_roles(
    boto3_session: boto3.session.Session,
    instance_arn: str,
    permission_set_arn: str,
    region: str,
) -> List[Dict]:
    """
    Get all accounts associated with a given permission set
    """
    client = boto3_session.client('sso-admin', region_name=region)
    accounts = []

    try:
        paginator = client.get_paginator('list_accounts_for_provisioned_permission_set')
        for page in paginator.paginate(InstanceArn=instance_arn, PermissionSetArn=permission_set_arn):
            accounts.extend(page.get('AccountIds', []))
    except client.exceptions.ClientError as e:
        logger.warning(f"Failed to get roles for permission set {permission_set_arn}: {e}")
        return []

    return accounts


@timeit
def load_permission_sets(
    neo4j_session: neo4j.Session,
    permission_sets: List[Dict],
    instance_arn: str,
    region: str,
    aws_update_tag: int,
) -> None:
    """
    Load Identity Center permission sets into the graph
    """
    logger.info(f"Loading {len(permission_sets)} permission sets for instance {instance_arn} in region {region}")

    load(
        neo4j_session,
        PermissionSetSchema(),
        permission_sets,
        lastupdated=aws_update_tag,
        InstanceArn=instance_arn,
        Region=region,
    )


@timeit
def get_permission_set_role_assignments(
    boto3_session: boto3.session.Session,
    instance_arn: str,
    permission_sets: List[Dict],
    region: str,
) -> List[Dict]:
    """
    Get role assignments for Identity Center permission sets
    """
    role_assignments = []
    for ps in permission_sets:
        permission_set_arn: str = ps.get('PermissionSetArn')
        accounts = get_permission_set_roles(boto3_session, instance_arn, permission_set_arn, region)
        for account_id in accounts:
            arn = f"arn:aws:iam::{account_id}:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_{ps.get('Name')}"
            role_assignments.append({
                'PermissionSetArn': ps.get('PermissionSetArn'),
                'RoleArn': arn,
            })
    return role_assignments


@timeit
def load_permission_set_role_assignments(
    neo4j_session: neo4j.Session,
    role_assignments: List[Dict],
    aws_update_tag: int,
) -> None:
    """
    Load Identity Center permission set role assignments into the graph
    """
    logger.info(f"Loading {len(role_assignments)} permission set role assignments")

    neo4j_session.run(
        """
        UNWIND $role_assignments AS ra
        MATCH (ps:AWSPermissionSet {arn: ra.PermissionSetArn})
        MATCH (role:AWSRole)
        WHERE role.arn STARTS WITH ra.RoleArn
        MERGE (ps)-[r:ASSIGNED_TO_ROLE]->(role)
        SET r.lastupdated = $aws_update_tag
        """,
        role_assignments=role_assignments,
        aws_update_tag=aws_update_tag,
    )


@timeit
def get_sso_users(boto3_session: boto3.session.Session, identity_store_id: str, region: str) -> List[Dict]:
    """
    Get all SSO users for a given Identity Store
    """
    client = boto3_session.client('identitystore', region_name=region)
    users = []

    try:
        paginator = client.get_paginator('list_users')
        for page in paginator.paginate(IdentityStoreId=identity_store_id):
            user_page = page.get('Users', [])
            for user in user_page:
                if user.get('ExternalIds', None):
                    user['ExternalId'] = user.get('ExternalIds')[0].get('Id')
                users.append(user)
    except client.exceptions.ClientError as e:
        logger.warning(f"Failed to get SSO users for identity store {identity_store_id} in region {region}: {e}")
        return []

    return users


@timeit
def load_sso_users(
    neo4j_session: neo4j.Session,
    users: List[Dict],
    identity_store_id: str,
    region: str,
    aws_update_tag: int,
) -> None:
    """
    Load SSO users into the graph
    """
    logger.info(f"Loading {len(users)} SSO users for identity store {identity_store_id} in region {region}")

    load(
        neo4j_session,
        SSOUserSchema(),
        users,
        lastupdated=aws_update_tag,
        IdentityStoreId=identity_store_id,
        Region=region,
    )


@timeit
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
        try:
            paginator = client.get_paginator('list_account_assignments_for_principal')
            for page in paginator.paginate(InstanceArn=instance_arn, PrincipalId=user_id, PrincipalType='USER'):
                for assignment in page.get('AccountAssignments', []):
                    role_assignments.append({
                        'UserId': user_id,
                        'PermissionSetArn': assignment.get('PermissionSetArn'),
                        'AccountId': assignment.get('AccountId'),
                    })
        except client.exceptions.ClientError as e:
            logger.warning(f"Failed to get account assignments for user {user_id}: {e}")

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
                update_tag,
            )

            permission_set_assignments = get_permission_set_role_assignments(
                boto3_session,
                instance_arn,
                permission_sets,
                region,
            )
            load_permission_set_role_assignments(neo4j_session, permission_set_assignments, update_tag)

            users = get_sso_users(boto3_session, identity_store_id, region)
            load_sso_users(
                neo4j_session,
                users,
                identity_store_id,
                region,
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

    cleanup_identity_center_instances(neo4j_session, common_job_parameters)
