import copy
import enum
import json
import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.intel.aws.iam import load_policy_data
from cartography.intel.aws.iam import transform_policy_data
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


class PolicyType(enum.Enum):
    managed = "managed"
    inline = "inline"


def get_boto3_client(boto3_session: boto3.session.Session, service: str, region: str):
    client = boto3_session.client(service, region_name=region, config=get_botocore_config())
    return client


@timeit
def get_identity_center_instances_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    instances: List[Dict] = []
    try:
        client = get_boto3_client(boto3_session, "sso-admin", region)

        paginator = client.get_paginator("list_instances")
        for page in paginator.paginate():
            instances.extend(page["Instances"])

    except Exception as e:
        logger.warning(
            f"Could not list identity center instances. skipping. - {e}",
        )
    return instances


@timeit
def load_identity_center_instance(
    neo4j_session: neo4j.Session,
    instance: Dict,
    update_tag: int,
    organization_id: str,
) -> None:
    neo4j_session.execute_write(_load_identity_center_instance_tx, instance, update_tag, organization_id)


@timeit
def _load_identity_center_instance_tx(
    tx: neo4j.Transaction,
    instance: Dict,
    update_tag: int,
    organization_id: str,
) -> None:
    ingest_instances = """
        MATCH (i:AWSOrganization{id: $ORGANIZATION_ID})
        SET
            i.firstseen = timestamp(),
            i.created_date = $instance.CreatedDate,
            i.identity_store_id = $instance.IdentityStoreId,
            i.identity_store_arn = $instance.InstanceArn,
            i.is_sso = true,
            i.lastupdated = $update_tag,
            i.name = $instance.Name
    """

    tx.run(
        ingest_instances,
        instance=instance,
        ORGANIZATION_ID=organization_id,
        update_tag=update_tag,
    )


@timeit
def get_identity_center_permissions_sets_list(
    boto3_session: boto3.session.Session,
    instance: Dict,
    region: str,
) -> List[Dict]:
    client = get_boto3_client(boto3_session, "sso-admin", region)
    iam_client = get_boto3_client(boto3_session, "iam", region)
    iam_resource = boto3_session.resource("iam")

    permission_sets: List[str] = []
    try:
        paginator = client.get_paginator("list_permission_sets")

        for page in paginator.paginate(InstanceArn=instance["InstanceArn"]):
            permission_sets.extend(page["PermissionSets"])

    except Exception as e:
        logger.warning(
            f"Could not list permission sets for {instance['InstanceArn']}. skipping. - {e}",
        )

    permission_sets_list: List[Dict] = []
    for permission_set in permission_sets:
        try:
            response = client.describe_permission_set(
                InstanceArn=instance["InstanceArn"],
                PermissionSetArn=permission_set,
            )
            permission_sets_list.append(response["PermissionSet"])

        except Exception as e:
            logger.warning(
                f"Could not get permission set info for {instance['InstanceArn']} - {permission_set}. skipping. - {e}",
            )

    return permission_sets_list


@timeit
def load_identity_center_permissions_sets(
    neo4j_session: neo4j.Session,
    instance_arn: str,
    permissions_sets_list: List[Dict],
    update_tag: int,
) -> None:
    neo4j_session.execute_write(
        _load_identity_center_permissions_sets_tx,
        instance_arn,
        permissions_sets_list,
        update_tag,
    )


@timeit
def _load_identity_center_permissions_sets_tx(
    tx: neo4j.Transaction,
    instance_arn: str,
    permissions_sets_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_permissions_sets = """
    UNWIND $permissions_sets_list AS permissions_set
        MERGE (p:AWSPermissionSet{arn: permissions_set.PermissionSetArn})
        ON CREATE SET
            p:AWSPrincipal,
            p.firstseen = timestamp(),
            p.created_date = permissions_set.CreatedDate
        SET
            p.lastupdated = $update_tag,
            p.id = permissions_set.id,
            p.name = permissions_set.Name,
            p.is_sso = true,
            p.description = permissions_set.Description,
            p.session_duration = permissions_set.SessionDuration,
            p.relay_state = permissions_set.RelayState
        WITH p
            MATCH (i:AWSOrganization{identity_store_arn: $INSTANCE_ARN})
            MERGE (i)-[r:RESOURCE]->(p)
            ON CREATE SET
                r.firstseen = timestamp()
            SET
                r.lastupdated = $update_tag
    """

    tx.run(
        ingest_permissions_sets,
        permissions_sets_list=permissions_sets_list,
        INSTANCE_ARN=instance_arn,
        update_tag=update_tag,
    )


@timeit
def get_managed_policies(
    boto3_session: boto3.session.Session,
    instance_arn: str,
    permission_sets: List[Dict],
    region: str,
):
    managed_policies: Dict = {}

    client = get_boto3_client(boto3_session, "sso-admin", region)
    iam_client = get_boto3_client(boto3_session, "iam", region)
    iam_resource = boto3_session.resource("iam")

    for permission_set in permission_sets:
        permission_set_arn = permission_set["PermissionSetArn"]
        permission_set_id = permission_set.get("id")

        policies: List[Dict] = []
        if permission_set_id:
            managed_policy_key = permission_set_id

        else:
            managed_policy_key = permission_set_arn

        managed_policies[managed_policy_key] = {}
        try:
            paginator = client.get_paginator("list_managed_policies_in_permission_set")
            for page in paginator.paginate(InstanceArn=instance_arn, PermissionSetArn=permission_set_arn):
                policies.extend(page["AttachedManagedPolicies"])

        except Exception as e:
            logger.warning(
                f"Could not get policies for permission set {instance_arn} - {permission_set_arn}; skipping. - {e}",
            )

        for policy in policies:
            try:
                policy.update(iam_client.get_policy(PolicyArn=policy["Arn"])["Policy"])
                managed_policies[managed_policy_key][policy["PolicyName"]] = iam_resource.PolicyVersion(
                    policy["Arn"],
                    policy["DefaultVersionId"],
                ).document["Statement"]

            except Exception as e:
                logger.warning(
                    f"Could not get policy info {policy['Arn']}; skipping. - {e}",
                )

    return managed_policies


@timeit
def get_inline_policy(boto3_session: boto3.session.Session, instance_arn: str, permission_sets: dict, region: str):
    client = get_boto3_client(boto3_session, "sso-admin", region)

    inline_policies: Dict = {}
    for permission_set in permission_sets:
        name = permission_set["Name"]
        permission_set_arn = permission_set["PermissionSetArn"]
        permission_set_id = permission_set.get("id")

        if permission_set_id:
            inline_policy_key = permission_set_id

        else:
            inline_policy_key = permission_set_arn

        inline_policy = ""
        try:
            inline_policy = client.get_inline_policy_for_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=permission_set_arn,
            ).get("InlinePolicy")

        except Exception as e:
            logger.warning(f"Could not get inline policy for {instance_arn} - {permission_set_arn}; skipping. - {e}")

        if inline_policy:
            inline_policy = json.loads(inline_policy)
            inline_policies[inline_policy_key] = {name: inline_policy["Statement"]}

    return inline_policies


@timeit
def get_list_account_assignments(
    boto3_session: boto3.session.Session,
    instance_arn: str,
    permission_set_arn: str,
    current_aws_account_id: str,
    region: str,
):
    client = get_boto3_client(boto3_session, "sso-admin", region)
    assignments: List[Dict] = []

    try:
        paginator = client.get_paginator("list_account_assignments")
        for page in paginator.paginate(
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn,
            AccountId=current_aws_account_id,
        ):
            assignments.extend(page["AccountAssignments"])

    except Exception as e:
        logger.warning(
            f"Could not list account assignments for {instance_arn} - {permission_set_arn} - {current_aws_account_id}; skipping. - {e}",
        )

    return assignments


@timeit
def get_list_account_assignments_for_principal(
    client: boto3.session.Session,
    instance_arn: str,
    principal_id: str,
    principal_type: str,
    region: str,
):
    assignments: List[Dict] = []

    try:
        paginator = client.get_paginator("list_account_assignments_for_principal")
        for page in paginator.paginate(
            InstanceArn=instance_arn,
            PrincipalId=principal_id,
            PrincipalType=principal_type,
        ):
            assignments.extend(page["AccountAssignments"])

    except Exception as e:
        logger.warning(
            f"Could not list account assignments for {instance_arn} - {principal_id} - {principal_type}; skipping. - {e}",
        )

    return assignments


@timeit
def load_identity_center_account_assignments(
    neo4j_session: neo4j.Session,
    assignments: List[Dict],
    permissions_sets: List[Dict],
    instance_arn: str,
    managed_policies: Dict,
    inline_policies: Dict,
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> List[str]:
    loaded_permissions_sets = []
    for assignment in assignments:
        for permissions_set in permissions_sets:
            if permissions_set["PermissionSetArn"] == assignment["PermissionSetArn"]:
                permissions_set_id = f"{assignment['PrincipalId']}/{permissions_set['Name']}"

                neo4j_session.execute_write(
                    _load_identity_center_account_assignments_tx, assignment, permissions_set, instance_arn, update_tag,
                )

                # INFO: This is a temporary solution to skip Loading Policies for manual runs.
                if common_job_parameters.get("MANUAL_RUN", False) or current_aws_account_id == "934101271236":
                    loaded_permissions_sets.append(permissions_set["PermissionSetArn"])
                    break

                if managed_policies.get(permissions_set.get("PermissionSetArn")):
                    permissions_set_managed_policies = {
                        permissions_set_id: copy.deepcopy(managed_policies.get(permissions_set["PermissionSetArn"], {})),
                    }
                    transform_policy_data(permissions_set_managed_policies, PolicyType.managed.value, current_aws_account_id)
                    load_policy_data(
                        neo4j_session,
                        permissions_set_managed_policies,
                        PolicyType.managed.value,
                        current_aws_account_id,
                        update_tag,
                    )
                if inline_policies.get(permissions_set.get("PermissionSetArn")):
                    permissions_set_inline_policies = {
                        permissions_set_id: copy.deepcopy(inline_policies.get(permissions_set["PermissionSetArn"], {})),
                    }
                    transform_policy_data(permissions_set_inline_policies, PolicyType.inline.value, current_aws_account_id)
                    load_policy_data(
                        neo4j_session,
                        permissions_set_inline_policies,
                        PolicyType.inline.value,
                        current_aws_account_id,
                        update_tag,
                    )
                loaded_permissions_sets.append(permissions_set["PermissionSetArn"])

                break
    return loaded_permissions_sets


@timeit
def _load_identity_center_account_assignments_tx(
    tx: neo4j.Transaction,
    assignment: Dict,
    permissions_set: Dict,
    instance_arn: str,
    update_tag: int,
) -> None:
    permissions_set_id = f"{assignment['PrincipalId']}/{permissions_set['Name']}"
    attach_permission_set_to_account = """
                MERGE (p:AWSPermissionSet{id: $permissions_set_id})
                    ON CREATE SET
                        p:AWSPrincipal,
                        p.firstseen = timestamp(),
                        p.created_date = $permissions_set.CreatedDate,
                        p.relay_state = $permissions_set.RelayState,
                        p.is_sso = true
                    SET
                        p.lastupdated = $update_tag,
                        p.name = $permissions_set.Name,
                        p.arn = $permissions_set.PermissionSetArn,
                        p.session_duration = $permissions_set.SessionDuration
                MERGE (a:AWSAccount{id: $assignment.AccountId})
                    ON CREATE SET
                        a.firstseen = timestamp()
                    SET
                        a.lastupdated = $update_tag
                WITH p,a
                    MERGE (p)-[r:ATTACHED_TO]->(a)
                    ON CREATE SET
                        r.firstseen = timestamp()
                    SET
                        r.lastupdated = $update_tag
                WITH p
                MATCH (i:AWSOrganization{identity_store_arn: $INSTANCE_ARN})
                MERGE (i)-[r1:RESOURCE]->(p)
                    ON CREATE SET
                        r1.firstseen = timestamp()
                    SET
                        r1.lastupdated = $update_tag
            """
    tx.run(
        attach_permission_set_to_account,
        assignment=assignment,
        permissions_set=permissions_set,
        permissions_set_id=permissions_set_id,
        INSTANCE_ARN=instance_arn,
        update_tag=update_tag,
    )

    ingest_assignment = """
                MATCH (p:AWSPermissionSet{id: $permissions_set_id})
                MATCH (pr:AWSPrincipal{id: $assignment.PrincipalId})
                WITH p,pr
                MERGE (p)-[r:ASSIGNED_TO]->(pr)
                ON CREATE SET
                        r.firstseen = timestamp()
                SET
                        r.lastupdated = $update_tag
            """

    tx.run(
        ingest_assignment,
        assignment=assignment,
        permissions_set_id=permissions_set_id,
        update_tag=update_tag,
    )


def transform_permission_sets(permissions_sets: list[dict]) -> list[dict]:
    items = []
    for permission_set in permissions_sets:
        permission_set["id"] = permission_set.get("PermissionSetArn", "").split("/")[-1]
        items.append(permission_set)

    return items


@timeit
def sync_identity_center_permissions_sets(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    instance: Dict,
    aws_update_tag: int,
    region: str,
    current_aws_account_id: str,
    common_job_parameters: Dict,
) -> None:
    permissions_sets = get_identity_center_permissions_sets_list(boto3_session, instance, region)

    # INFO: This is a temporary solution to skip Loading Policies for manual runs.
    if common_job_parameters.get("MANUAL_RUN", False) or current_aws_account_id == "934101271236":
        managed_policies = {}
        inline_policies = {}

    else:
        managed_policies = get_managed_policies(boto3_session, instance["InstanceArn"], permissions_sets, region)
        inline_policies = get_inline_policy(boto3_session, instance["InstanceArn"], permissions_sets, region)

    users = get_identity_center_users_list(boto3_session, instance, region)
    groups = get_identity_center_groups_list(boto3_session, instance, region)
    client = get_boto3_client(boto3_session, "sso-admin", region)
    loaded_permissions_sets = []

    for user in users:
        assignments = get_list_account_assignments_for_principal(
            client,
            instance["InstanceArn"],
            user["UserId"],
            "USER",
            region,
        )
        loaded_permissions_sets.extend(
            load_identity_center_account_assignments(
                neo4j_session,
                assignments,
                permissions_sets,
                instance["InstanceArn"],
                managed_policies,
                inline_policies,
                current_aws_account_id,
                aws_update_tag,
                common_job_parameters,
            ),
        )
    for group in groups:
        assignments = get_list_account_assignments_for_principal(
            client,
            instance["InstanceArn"],
            group["GroupId"],
            "GROUP",
            region,
        )
        loaded_permissions_sets.extend(
            load_identity_center_account_assignments(
                neo4j_session,
                assignments,
                permissions_sets,
                instance["InstanceArn"],
                managed_policies,
                inline_policies,
                current_aws_account_id,
                aws_update_tag,
                common_job_parameters,
            ),
        )

    unloaded_permissions_sets = []
    unloaded_managed_policies = {}
    unloaded_inline_policies = {}
    for permissions_set in permissions_sets:
        if permissions_set["PermissionSetArn"] in loaded_permissions_sets:
            continue

        unloaded_permissions_sets.append(permissions_set)
        # INFO: This is a temporary solution to skip Loading Policies for manual runs.
        if common_job_parameters.get("MANUAL_RUN", False) or current_aws_account_id == "934101271236":
            continue
        unloaded_managed_policies[permissions_set["PermissionSetArn"]] = copy.deepcopy(managed_policies.get(permissions_set["PermissionSetArn"], {}))
        unloaded_inline_policies[permissions_set["PermissionSetArn"]] = copy.deepcopy(inline_policies.get(permissions_set["PermissionSetArn"], {}))

    load_identity_center_permissions_sets(
        neo4j_session,
        instance["InstanceArn"],
        unloaded_permissions_sets,
        aws_update_tag,
    )

    transform_policy_data(unloaded_managed_policies, PolicyType.managed.value, current_aws_account_id)
    load_policy_data(neo4j_session, unloaded_managed_policies, PolicyType.managed.value, current_aws_account_id, aws_update_tag)
    transform_policy_data(unloaded_inline_policies, PolicyType.inline.value, current_aws_account_id)
    load_policy_data(neo4j_session, unloaded_inline_policies, PolicyType.inline.value, current_aws_account_id, aws_update_tag)


@timeit
def get_identity_center_users_list(boto3_session: boto3.session.Session, instance: Dict, region: str) -> List[Dict]:
    client = get_boto3_client(boto3_session, "identitystore", region)

    users: List[Dict] = []
    try:
        paginator = client.get_paginator("list_users")

        for page in paginator.paginate(IdentityStoreId=instance["IdentityStoreId"]):
            users.extend(page["Users"])

    except Exception as e:
        logger.warning(
            f"Could not list users for {instance['IdentityStoreId']}. skipping. - {e}",
        )

    for user in users:
        user["arn"] = f"{instance['InstanceArn']}/user/{user['UserId']}"

    return users


@timeit
def load_identity_center_users(
    neo4j_session: neo4j.Session,
    instance_arn: str,
    users_list: List[Dict],
    update_tag: int,
) -> None:
    neo4j_session.execute_write(_load_identity_center_users_tx, instance_arn, users_list, update_tag)


@timeit
def _load_identity_center_users_tx(
    tx: neo4j.Transaction,
    instance_arn: str,
    users_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_users = """
    UNWIND $users_list AS user
        MERGE (u:AWSUser{userid: user.UserId})
        ON CREATE SET
            u:AWSPrincipal,
            u.firstseen = timestamp(),
            u.user_name = user.UserName,
            u.user_type = user.UserType,
            u.is_sso = true,
            u.identity_store_id = user.IdentityStoreId,
            u.id = user.UserId,
            u.arn = user.arn
        SET
            u.lastupdated = $update_tag,
            u.name = user.DisplayName
        WITH u
            MATCH (i:AWSOrganization{identity_store_arn: $INSTANCE_ARN})
            MERGE (i)-[r:RESOURCE]->(u)
            ON CREATE SET
                r.firstseen = timestamp()
            SET
                r.lastupdated = $update_tag
    """

    tx.run(
        ingest_users,
        users_list=users_list,
        INSTANCE_ARN=instance_arn,
        update_tag=update_tag,
    )


@timeit
def sync_identity_center_users(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    instance: Dict,
    aws_update_tag: int,
    region: str,
) -> None:
    users = get_identity_center_users_list(boto3_session, instance, region)
    load_identity_center_users(neo4j_session, instance["InstanceArn"], users, aws_update_tag)


@timeit
def get_identity_center_groups_list(boto3_session: boto3.session.Session, instance: Dict, region: str) -> List[Dict]:
    client = get_boto3_client(boto3_session, "identitystore", region)

    groups: List[Dict] = []
    try:
        paginator = client.get_paginator("list_groups")

        for page in paginator.paginate(IdentityStoreId=instance["IdentityStoreId"]):
            groups.extend(page["Groups"])

    except Exception as e:
        logger.warning(
            f"Could not list groups for {instance['IdentityStoreId']}. skipping. - {e}",
        )

    for group in groups:
        group["arn"] = f"{instance['InstanceArn']}/group/{group['GroupId']}"

    return groups


@timeit
def load_identity_center_groups(
    neo4j_session: neo4j.Session,
    instance_arn: str,
    groups_list: List[Dict],
    update_tag: int,
) -> None:
    neo4j_session.execute_write(_load_identity_center_groups_tx, instance_arn, groups_list, update_tag)


@timeit
def _load_identity_center_groups_tx(
    tx: neo4j.Transaction,
    instance_arn: str,
    groups_list: List[Dict],
    update_tag: int,
) -> None:
    ingest_groups = """
    UNWIND $groups_list AS group
        MERGE (g:AWSGroup{groupid: group.GroupId})
        ON CREATE SET
            g:AWSPrincipal,
            g.firstseen = timestamp(),
            g.identity_store_id = group.IdentityStoreId,
            g.id = group.GroupId,
            g.arn = group.arn
        SET
            g.lastupdated = $update_tag,
            g.is_sso = true,
            g.name = group.DisplayName
        WITH g
            MATCH (i:AWSOrganization{identity_store_arn: $INSTANCE_ARN})
            MERGE (i)-[r:RESOURCE]->(g)
            ON CREATE SET
                r.firstseen = timestamp()
            SET
                r.lastupdated = $update_tag
    """

    tx.run(
        ingest_groups,
        groups_list=groups_list,
        INSTANCE_ARN=instance_arn,
        update_tag=update_tag,
    )


@timeit
def get_list_group_memberships(
    boto3_session: boto3.session.Session,
    group: str,
    instance: Dict,
    region: str,
) -> List[Dict]:
    client = get_boto3_client(boto3_session, "identitystore", region)

    group_memberships: List[Dict] = []
    try:
        paginator = client.get_paginator("list_group_memberships")

        for page in paginator.paginate(IdentityStoreId=instance["IdentityStoreId"], GroupId=group["GroupId"]):
            group_memberships.extend(page["GroupMemberships"])

    except Exception as e:
        logger.warning(
            f"Could not list group memberships for {instance['IdentityStoreId']} - {group['GroupId']}. skipping. - {e}",
        )

    return group_memberships


@timeit
def load_identity_center_group_memberships(
    neo4j_session: neo4j.Session,
    memberships: List[Dict],
    update_tag: int,
) -> None:
    neo4j_session.execute_write(_load_identity_center_group_memberships_tx, memberships, update_tag)


@timeit
def _load_identity_center_group_memberships_tx(tx: neo4j.Transaction, memberships: List[Dict], update_tag: int) -> None:
    ingest_memberships = """
    UNWIND $memberships AS membership
        MATCH (p:AWSGroup{id: membership.GroupId})
        MATCH (pr:AWSUser{id: membership.MemberId.UserId})
        WITH p,pr
        MERGE (pr)-[r:MEMBER_AWS_GROUP]->(p)
        ON CREATE SET
                r.firstseen = timestamp()
        SET
                r.lastupdated = $update_tag
    """

    tx.run(
        ingest_memberships,
        memberships=memberships,
        update_tag=update_tag,
    )


@timeit
def sync_identity_center_groups(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    instance: Dict,
    aws_update_tag: int,
    region: str,
) -> None:
    groups = get_identity_center_groups_list(boto3_session, instance, region)
    load_identity_center_groups(neo4j_session, instance["InstanceArn"], groups, aws_update_tag)
    for group in groups:
        group_memberships = get_list_group_memberships(boto3_session, group, instance, region)
        load_identity_center_group_memberships(neo4j_session, group_memberships, aws_update_tag)


def cleanup_identitystore(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("aws_import_identitystore_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync_identitystore(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    region: str = common_job_parameters["IDENTITY_STORE_REGION"]
    organization_id = common_job_parameters["ORGANIZATION_ID"]
    instances = get_identity_center_instances_list(boto3_session, common_job_parameters["IDENTITY_STORE_REGION"])
    for instance in instances:
        load_identity_center_instance(
            neo4j_session,
            instance,
            aws_update_tag,
            organization_id,
        )
        sync_identity_center_users(neo4j_session, boto3_session, instance, aws_update_tag, region)
        sync_identity_center_groups(neo4j_session, boto3_session, instance, aws_update_tag, region)
        sync_identity_center_permissions_sets(
            neo4j_session, boto3_session, instance, aws_update_tag, region, current_aws_account_id, common_job_parameters,
        )

    cleanup_identitystore(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()
    sync_identitystore(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    toc = time.perf_counter()
    logger.info(f"Time to process identitystore: {toc - tic:0.4f} seconds")
