import enum
import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.intel.aws.permission_relationships import parse_statement_node
from cartography.intel.aws.permission_relationships import principal_allowed_on_resource
from cartography.models.aws.iam.policy import AWSPolicySchema
from cartography.models.aws.iam.policy_statement import AWSPolicyStatementSchema
from cartography.models.aws.iam.user import AWSUserSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

# Overview of IAM in AWS
# https://aws.amazon.com/iam/


class PolicyType(enum.Enum):
    managed = "managed"
    inline = "inline"


def get_policy_name_from_arn(arn: str) -> str:
    return arn.split("/")[-1]


@timeit
def get_group_policies(boto3_session: boto3.Session, group_name: str) -> Dict:
    client = boto3_session.client("iam")
    paginator = client.get_paginator("list_group_policies")
    policy_names: List[Dict] = []
    for page in paginator.paginate(GroupName=group_name):
        policy_names.extend(page["PolicyNames"])
    return {"PolicyNames": policy_names}


@timeit
def get_group_policy_info(
    boto3_session: boto3.Session,
    group_name: str,
    policy_name: str,
) -> Any:
    client = boto3_session.client("iam")
    return client.get_group_policy(GroupName=group_name, PolicyName=policy_name)


@timeit
def get_group_membership_data(
    boto3_session: boto3.Session,
    group_name: str,
) -> Dict:
    client = boto3_session.client("iam")
    try:
        memberships = client.get_group(GroupName=group_name)
        return memberships
    except client.exceptions.NoSuchEntityException:
        # Avoid crashing the sync
        logger.warning(
            "client.get_group(GroupName='%s') failed with NoSuchEntityException; skipping.",
            group_name,
        )
        return {}


@timeit
def get_group_policy_data(
    boto3_session: boto3.Session,
    group_list: List[Dict],
) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for group in group_list:
        name = group["GroupName"]
        arn = group["Arn"]
        resource_group = resource_client.Group(name)
        policies[arn] = policies[arn] = {
            p.name: p.policy_document["Statement"]
            for p in resource_group.policies.all()
        }
    return policies


@timeit
def get_group_managed_policy_data(
    boto3_session: boto3.Session,
    group_list: List[Dict],
) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for group in group_list:
        name = group["GroupName"]
        group_arn = group["Arn"]
        resource_group = resource_client.Group(name)
        policies[group_arn] = {
            p.arn: p.default_version.document["Statement"]
            for p in resource_group.attached_policies.all()
        }
    return policies


@timeit
def get_user_policy_data(
    boto3_session: boto3.Session,
    user_list: List[Dict],
) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for user in user_list:
        name = user["UserName"]
        arn = user["Arn"]
        resource_user = resource_client.User(name)
        try:
            policies[arn] = {
                p.name: p.policy_document["Statement"]
                for p in resource_user.policies.all()
            }
        except resource_client.meta.client.exceptions.NoSuchEntityException:
            logger.warning(
                f"Could not get policies for user {name} due to NoSuchEntityException; skipping.",
            )
    return policies


@timeit
def get_user_managed_policy_data(
    boto3_session: boto3.Session,
    user_list: List[Dict],
) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for user in user_list:
        name = user["UserName"]
        user_arn = user["Arn"]
        resource_user = resource_client.User(name)
        try:
            policies[user_arn] = {
                p.arn: p.default_version.document["Statement"]
                for p in resource_user.attached_policies.all()
            }
        except resource_client.meta.client.exceptions.NoSuchEntityException:
            logger.warning(
                f"Could not get policies for user {name} due to NoSuchEntityException; skipping.",
            )
    return policies


@timeit
def get_role_policy_data(
    boto3_session: boto3.Session,
    role_list: List[Dict],
) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for role in role_list:
        name = role["RoleName"]
        arn = role["Arn"]
        resource_role = resource_client.Role(name)
        try:
            policies[arn] = {
                p.name: p.policy_document["Statement"]
                for p in resource_role.policies.all()
            }
        except resource_client.meta.client.exceptions.NoSuchEntityException:
            logger.warning(
                f"Could not get policies for role {name} due to NoSuchEntityException; skipping.",
            )
    return policies


@timeit
def get_role_managed_policy_data(
    boto3_session: boto3.Session,
    role_list: List[Dict],
) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for role in role_list:
        name = role["RoleName"]
        role_arn = role["Arn"]
        resource_role = resource_client.Role(name)
        try:
            policies[role_arn] = {
                p.arn: p.default_version.document["Statement"]
                for p in resource_role.attached_policies.all()
            }
        except resource_client.meta.client.exceptions.NoSuchEntityException:
            logger.warning(
                f"Could not get policies for role {name} due to NoSuchEntityException; skipping.",
            )
    return policies


@timeit
def get_role_tags(boto3_session: boto3.Session) -> List[Dict]:
    role_list = get_role_list_data(boto3_session)["Roles"]
    resource_client = boto3_session.resource("iam")
    role_tag_data: List[Dict] = []
    for role in role_list:
        name = role["RoleName"]
        role_arn = role["Arn"]
        resource_role = resource_client.Role(name)
        role_tags = resource_role.tags
        if not role_tags:
            continue

        tag_data = {
            "ResourceARN": role_arn,
            "Tags": resource_role.tags,
        }
        role_tag_data.append(tag_data)

    return role_tag_data


@timeit
def get_user_list_data(boto3_session: boto3.Session) -> Dict:
    client = boto3_session.client("iam")

    paginator = client.get_paginator("list_users")
    users: List[Dict] = []
    for page in paginator.paginate():
        users.extend(page["Users"])
    return {"Users": users}


@timeit
def get_group_list_data(boto3_session: boto3.Session) -> Dict:
    client = boto3_session.client("iam")
    paginator = client.get_paginator("list_groups")
    groups: List[Dict] = []
    for page in paginator.paginate():
        groups.extend(page["Groups"])
    return {"Groups": groups}


@timeit
def get_role_list_data(boto3_session: boto3.Session) -> Dict:
    client = boto3_session.client("iam")
    paginator = client.get_paginator("list_roles")
    roles: List[Dict] = []
    for page in paginator.paginate():
        roles.extend(page["Roles"])
    return {"Roles": roles}


@timeit
def get_account_access_key_data(
    boto3_session: boto3.Session,
    username: str,
) -> Dict:
    client = boto3_session.client("iam")
    # NOTE we can get away without using a paginator here because users are limited to two access keys
    access_keys: Dict = {}
    try:
        access_keys = client.list_access_keys(UserName=username)
    except client.exceptions.NoSuchEntityException:
        logger.warning(
            f"Could not get access key for user {username} due to NoSuchEntityException; skipping.",
        )
        return access_keys
    for access_key in access_keys["AccessKeyMetadata"]:
        access_key_id = access_key["AccessKeyId"]
        last_used_info = client.get_access_key_last_used(
            AccessKeyId=access_key_id,
        )["AccessKeyLastUsed"]
        # only LastUsedDate may be null
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam/client/get_access_key_last_used.html
        access_key["LastUsedDate"] = last_used_info.get("LastUsedDate")
        access_key["LastUsedService"] = last_used_info["ServiceName"]
        access_key["LastUsedRegion"] = last_used_info["Region"]
    return access_keys


def transform_users(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform AWS IAM user data for schema-based loading.
    """
    user_data = []
    for user in users:
        user_record = {
            "arn": user["Arn"],
            "userid": user["UserId"],
            "name": user["UserName"],
            "path": user["Path"],
            "createdate": str(user["CreateDate"]),
            "passwordlastused": str(user.get("PasswordLastUsed", "")),
        }
        user_data.append(user_record)

    return user_data


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    users: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSUserSchema(),
        users,
        lastupdated=aws_update_tag,
        AWS_ACCOUNT_ID=current_aws_account_id,
    )


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    groups: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_group = """
    MERGE (gnode:AWSGroup{arn: $ARN})
    ON CREATE SET gnode.groupid = $GROUP_ID, gnode.firstseen = timestamp(), gnode.createdate = $CREATE_DATE
    SET gnode:AWSPrincipal, gnode.name = $GROUP_NAME, gnode.path = $PATH,gnode.lastupdated = $aws_update_tag
    WITH gnode
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(gnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    logger.info(f"Loading {len(groups)} IAM groups to the graph.")
    for group in groups:
        neo4j_session.run(
            ingest_group,
            ARN=group["Arn"],
            GROUP_ID=group["GroupId"],
            CREATE_DATE=str(group["CreateDate"]),
            GROUP_NAME=group["GroupName"],
            PATH=group["Path"],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


def _parse_principal_entries(principal: Dict) -> List[Tuple[Any, Any]]:
    """
    Returns a list of tuples of the form (principal_type, principal_value)
    e.g. [('AWS', 'example-role-name'), ('Service', 'example-service')]
    """
    principal_entries = []
    for principal_type in principal:
        principal_values = principal[principal_type]
        if not isinstance(principal_values, list):
            principal_values = [principal_values]
        for principal_value in principal_values:
            principal_entries.append((principal_type, principal_value))
    return principal_entries


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    roles: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_role = """
    MERGE (rnode:AWSPrincipal{arn: $Arn})
    ON CREATE SET rnode.firstseen = timestamp()
    SET
        rnode:AWSRole,
        rnode.roleid = $RoleId,
        rnode.createdate = $CreateDate,
        rnode.name = $RoleName,
        rnode.path = $Path,
        rnode.lastupdated = $aws_update_tag
    WITH rnode
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(rnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    ingest_policy_statement = """
    MERGE (spnnode:AWSPrincipal{arn: $SpnArn})
    ON CREATE SET spnnode.firstseen = timestamp()
    SET spnnode.lastupdated = $aws_update_tag, spnnode.type = $SpnType
    WITH spnnode
    MATCH (role:AWSRole{arn: $RoleArn})
    MERGE (role)-[r:TRUSTS_AWS_PRINCIPAL]->(spnnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    # Note - why we don't set inscope or foreign attribute on the account
    #
    # we are agnostic here if this is the AWSAccount is part of the sync scope or
    # a foreign AWS account that contains a trusted principal. The account could also be inscope
    # but not sync yet.
    # - The inscope attribute - set when the account is being sync.
    # - The foreign attribute - the attribute assignment logic is in aws_foreign_accounts.json analysis job
    # - Why seperate statement is needed - the arn may point to service level principals ex - ec2.amazonaws.com
    ingest_spnmap_statement = """
    MERGE (aa:AWSAccount{id: $SpnAccountId})
    ON CREATE SET aa.firstseen = timestamp()
    SET aa.lastupdated = $aws_update_tag
    WITH aa
    MATCH (spnnode:AWSPrincipal{arn: $SpnArn})
    WITH spnnode, aa
    MERGE (aa)-[r:RESOURCE]->(spnnode)
    ON CREATE SET r.firstseen = timestamp()
    """

    # TODO support conditions
    logger.info(f"Loading {len(roles)} IAM roles to the graph.")
    for role in roles:
        neo4j_session.run(
            ingest_role,
            Arn=role["Arn"],
            RoleId=role["RoleId"],
            CreateDate=str(role["CreateDate"]),
            RoleName=role["RoleName"],
            Path=role["Path"],
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        for statement in role["AssumeRolePolicyDocument"]["Statement"]:
            principal_entries = _parse_principal_entries(statement["Principal"])
            for principal_type, principal_value in principal_entries:
                neo4j_session.run(
                    ingest_policy_statement,
                    SpnArn=principal_value,
                    SpnType=principal_type,
                    RoleArn=role["Arn"],
                    aws_update_tag=aws_update_tag,
                )
                spn_arn = get_account_from_arn(principal_value)
                if spn_arn:
                    neo4j_session.run(
                        ingest_spnmap_statement,
                        SpnArn=principal_value,
                        SpnAccountId=get_account_from_arn(principal_value),
                        aws_update_tag=aws_update_tag,
                    )


@timeit
def load_group_memberships(
    neo4j_session: neo4j.Session,
    group_memberships: Dict,
    aws_update_tag: int,
) -> None:
    ingest_membership = """
    MATCH (group:AWSGroup{arn: $GroupArn})
    WITH group
    MATCH (user:AWSUser{arn: $PrincipalArn})
    MERGE (user)-[r:MEMBER_AWS_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    WITH user, group
    MATCH (group)-[:POLICY]->(policy:AWSPolicy)
    MERGE (user)-[r2:POLICY]->(policy)
    SET r2.lastupdated = $aws_update_tag
    """

    for group_arn, membership_data in group_memberships.items():
        for info in membership_data.get("Users", []):
            principal_arn = info["Arn"]
            neo4j_session.run(
                ingest_membership,
                GroupArn=group_arn,
                PrincipalArn=principal_arn,
                aws_update_tag=aws_update_tag,
            )


@timeit
def get_policies_for_principal(
    neo4j_session: neo4j.Session,
    principal_arn: str,
) -> Dict:
    get_policy_query = """
    MATCH
    (principal:AWSPrincipal{arn:$Arn})-[:POLICY]->
    (policy:AWSPolicy)-[:STATEMENT]->
    (statements:AWSPolicyStatement)
    RETURN
    DISTINCT policy.id AS policy_id,
    COLLECT(DISTINCT statements) AS statements
    """
    results = neo4j_session.run(
        get_policy_query,
        Arn=principal_arn,
    )
    policies = {r["policy_id"]: parse_statement_node(r["statements"]) for r in results}
    return policies


@timeit
def sync_assumerole_relationships(
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    # Must be called after load_role
    # Computes and syncs the STS_ASSUMEROLE_ALLOW relationship
    logger.info(
        "Syncing assume role mappings for account '%s'.",
        current_aws_account_id,
    )
    query_potential_matches = """
    MATCH (:AWSAccount{id:$AccountId})-[:RESOURCE]->(target:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(source:AWSPrincipal)
    WHERE NOT source.arn ENDS WITH 'root'
    AND NOT source.type = 'Service'
    AND NOT source.type = 'Federated'
    RETURN target.arn AS target_arn,
    source.arn AS source_arn
    """

    ingest_policies_assume_role = """
    MATCH (source:AWSPrincipal{arn: $SourceArn})
    WITH source
    MATCH (role:AWSRole{arn: $TargetArn})
    WITH role, source
    MERGE (source)-[r:STS_ASSUMEROLE_ALLOW]->(role)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    results = neo4j_session.run(
        query_potential_matches,
        AccountId=current_aws_account_id,
    )
    potential_matches = [(r["source_arn"], r["target_arn"]) for r in results]
    for source_arn, target_arn in potential_matches:
        policies = get_policies_for_principal(neo4j_session, source_arn)
        if principal_allowed_on_resource(policies, target_arn, ["sts:AssumeRole"]):
            neo4j_session.run(
                ingest_policies_assume_role,
                SourceArn=source_arn,
                TargetArn=target_arn,
                aws_update_tag=aws_update_tag,
            )
    run_cleanup_job(
        "aws_import_roles_policy_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def load_user_access_keys(
    neo4j_session: neo4j.Session,
    user_access_keys: Dict,
    aws_update_tag: int,
) -> None:
    # TODO change the node label to reflect that this is a user access key, not an account access key
    ingest_account_key = """
    MATCH (user:AWSUser{arn: $UserARN})
    WITH user
    MERGE (key:AccountAccessKey{accesskeyid: $AccessKeyId})
    ON CREATE SET key.firstseen = timestamp(), key.createdate = $CreateDate
    SET key.status = $Status,
        key.lastupdated = $aws_update_tag,
        key.lastuseddate = $LastUsedDate,
        key.lastusedservice = $LastUsedService,
        key.lastusedregion = $LastUsedRegion
    WITH user,key
    MERGE (user)-[r:AWS_ACCESS_KEY]->(key)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    for arn, access_keys in user_access_keys.items():
        for key in access_keys["AccessKeyMetadata"]:
            if key.get("AccessKeyId"):
                neo4j_session.run(
                    ingest_account_key,
                    UserARN=arn,
                    AccessKeyId=key["AccessKeyId"],
                    CreateDate=str(key["CreateDate"]),
                    Status=key["Status"],
                    LastUsedDate=key["LastUsedDate"],
                    LastUsedService=key["LastUsedService"],
                    LastUsedRegion=key["LastUsedRegion"],
                    aws_update_tag=aws_update_tag,
                )


def ensure_list(obj: Any) -> List[Any]:
    if not isinstance(obj, list):
        obj = [obj]
    return obj


def _transform_policy_statements(
    statements: Any, policy_id: str
) -> list[dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    count = 1

    if not isinstance(statements, list):
        statements = [statements]

    for stmt in statements:
        # Determine statement ID
        if "Sid" in stmt and stmt["Sid"]:
            statement_id = stmt["Sid"]
        else:
            statement_id = count
            count += 1

        transformed_stmt = {
            "id": f"{policy_id}/statement/{statement_id}",
            "policy_id": policy_id,  # For the relationship to AWSPolicy
            "Effect": stmt.get("Effect"),
            "Sid": stmt.get("Sid"),
        }

        # Handle list fields
        if "Resource" in stmt:
            transformed_stmt["Resource"] = ensure_list(stmt["Resource"])
        if "Action" in stmt:
            transformed_stmt["Action"] = ensure_list(stmt["Action"])
        if "NotAction" in stmt:
            transformed_stmt["NotAction"] = ensure_list(stmt["NotAction"])
        if "NotResource" in stmt:
            transformed_stmt["NotResource"] = ensure_list(stmt["NotResource"])
        if "Condition" in stmt:
            transformed_stmt["Condition"] = json.dumps(ensure_list(stmt["Condition"]))

        result.append(transformed_stmt)

    return result


def transform_policy_data(
    policy_map: Dict, policy_type: str
) -> Dict[str, Dict[str, list[dict[str, Any]]]]:
    transformed_policy_map: Dict[str, Dict[str, list[dict[str, Any]]]] = {}

    for principal_arn, policy_statement_map in policy_map.items():
        logger.debug(
            f"Transforming IAM {policy_type} policies for principal {principal_arn}",
        )
        transformed_policy_map[principal_arn] = {}

        for policy_key, statements in policy_statement_map.items():
            policy_id = (
                transform_policy_id(
                    principal_arn,
                    policy_type,
                    policy_key,
                )
                if policy_type == PolicyType.inline.value
                else policy_key
            )

            transformed_statements = _transform_policy_statements(
                statements,
                policy_id,
            )

            transformed_policy_map[principal_arn][policy_key] = transformed_statements

    return transformed_policy_map


def transform_policy_id(principal_arn: str, policy_type: str, name: str) -> str:
    return f"{principal_arn}/{policy_type}_policy/{name}"


def _load_policy_tx(
    tx: neo4j.Transaction,
    policy_id: str,
    policy_name: str,
    policy_type: str,
    principal_arn: str,
    aws_update_tag: int,
) -> None:
    ingest_policy = """
    MERGE (policy:AWSPolicy{id: $PolicyId})
    ON CREATE SET
        policy.firstseen = timestamp(),
        policy.type = $PolicyType,
        policy.name = $PolicyName
    SET policy.lastupdated = $aws_update_tag
    WITH policy
    MATCH (principal:AWSPrincipal{arn: $PrincipalArn})
    MERGE (policy) <-[r:POLICY]-(principal)
    SET r.lastupdated = $aws_update_tag
    """
    tx.run(
        ingest_policy,
        PolicyId=policy_id,
        PolicyName=policy_name,
        PolicyType=policy_type,
        PrincipalArn=principal_arn,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_policy(
    neo4j_session: neo4j.Session,
    policy_id: str,
    policy_name: str,
    policy_type: str,
    principal_arn: str,
    aws_update_tag: int,
) -> None:
    # TODO move this out to a transform when we break this interface.
    policy_data = [
        {
            "id": policy_id,
            "name": policy_name,
            "type": policy_type,
            "arn": policy_id if policy_type == PolicyType.managed.value else None,
            "createdate": None,  # Not available in current data
            "principal_arn": principal_arn,  # For relationship
        }
    ]

    _load_policy_with_schema(neo4j_session, policy_data, aws_update_tag)


@timeit
def _load_policy_with_schema(
    neo4j_session: neo4j.Session,
    policy_data: list[dict[str, Any]],
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSPolicySchema(),
        policy_data,
        lastupdated=aws_update_tag,
    )


@timeit
def load_policy_statements(
    neo4j_session: neo4j.Session,
    statements: list[dict[str, Any]],
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSPolicyStatementSchema(),
        statements,
        lastupdated=aws_update_tag,
    )


@timeit
def load_policy_data(
    neo4j_session: neo4j.Session,
    principal_policy_map: Dict[str, Dict[str, list[dict[str, Any]]]],
    policy_type: str,
    aws_update_tag: int,
) -> None:
    for principal_arn, policy_statement_map in principal_policy_map.items():
        logger.debug(f"Loading policies for principal {principal_arn}")
        for policy_key, statements in policy_statement_map.items():
            policy_name = (
                policy_key
                if policy_type == PolicyType.inline.value
                else get_policy_name_from_arn(policy_key)
            )
            policy_id = (
                transform_policy_id(
                    principal_arn,
                    policy_type,
                    policy_key,
                )
                if policy_type == PolicyType.inline.value
                else policy_key
            )

            # TODO: break this interface
            load_policy(
                neo4j_session,
                policy_id,
                policy_name,
                policy_type,
                principal_arn,
                aws_update_tag,
            )

            load_policy_statements(
                neo4j_session,
                statements,
                aws_update_tag,
            )


@timeit
def load_policy_data_with_schema(
    neo4j_session: neo4j.Session,
    principal_policy_map: Dict[str, Dict[str, list[dict[str, Any]]]],
    policy_type: str,
    aws_update_tag: int,
) -> None:
    """
    Load policies using the modern data model schema.
    This function maintains the same interface as the old load_policy_data function
    but uses the new AWSPolicySchema for better type safety and consistency.
    """
    from cartography.client.core.tx import load

    # Transform data for schema-based loading
    policy_data: list[dict[str, Any]] = []

    for principal_arn, policy_statement_map in principal_policy_map.items():
        logger.debug(f"Loading policies for principal {principal_arn}")
        for policy_key, statements in policy_statement_map.items():
            policy_name = (
                policy_key
                if policy_type == PolicyType.inline.value
                else get_policy_name_from_arn(policy_key)
            )
            policy_id = (
                transform_policy_id(
                    principal_arn,
                    policy_type,
                    policy_key,
                )
                if policy_type == PolicyType.inline.value
                else policy_key
            )

            # Transform to schema format
            policy_record = {
                "id": policy_id,
                "name": policy_name,
                "type": policy_type,
                "arn": policy_key if policy_type == PolicyType.managed.value else None,
                "createdate": None,  # Not available in current data
                "principal_arn": principal_arn,  # For relationship
            }
            policy_data.append(policy_record)

    # Load policies using schema
    if policy_data:
        load(
            neo4j_session,
            AWSPolicySchema(),
            policy_data,
            lastupdated=aws_update_tag,
        )

    # Load policy statements (unchanged)
    for principal_arn, policy_statement_map in principal_policy_map.items():
        for policy_key, statements in policy_statement_map.items():
            load_policy_statements(
                neo4j_session,
                statements,
                aws_update_tag,
            )


@timeit
def sync_users(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM users for account '%s'.", current_aws_account_id)
    data = get_user_list_data(boto3_session)
    user_data = transform_users(data["Users"])
    load_users(neo4j_session, user_data, current_aws_account_id, aws_update_tag)

    sync_user_inline_policies(boto3_session, data, neo4j_session, aws_update_tag)

    sync_user_managed_policies(boto3_session, data, neo4j_session, aws_update_tag)

    run_cleanup_job(
        "aws_import_users_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_user_managed_policies(
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
) -> None:
    managed_policy_data = get_user_managed_policy_data(boto3_session, data["Users"])
    transformed_policy_data = transform_policy_data(
        managed_policy_data, PolicyType.managed.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        PolicyType.managed.value,
        aws_update_tag,
    )


@timeit
def sync_user_inline_policies(
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
) -> None:
    policy_data = get_user_policy_data(boto3_session, data["Users"])
    transformed_policy_data = transform_policy_data(
        policy_data, PolicyType.inline.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        PolicyType.inline.value,
        aws_update_tag,
    )


@timeit
def sync_groups(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM groups for account '%s'.", current_aws_account_id)
    data = get_group_list_data(boto3_session)
    load_groups(neo4j_session, data["Groups"], current_aws_account_id, aws_update_tag)

    sync_groups_inline_policies(boto3_session, data, neo4j_session, aws_update_tag)

    sync_group_managed_policies(boto3_session, data, neo4j_session, aws_update_tag)

    run_cleanup_job(
        "aws_import_groups_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def sync_group_managed_policies(
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
) -> None:
    managed_policy_data = get_group_managed_policy_data(boto3_session, data["Groups"])
    transformed_policy_data = transform_policy_data(
        managed_policy_data, PolicyType.managed.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        PolicyType.managed.value,
        aws_update_tag,
    )


def sync_groups_inline_policies(
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
) -> None:
    policy_data = get_group_policy_data(boto3_session, data["Groups"])
    transformed_policy_data = transform_policy_data(
        policy_data, PolicyType.inline.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        PolicyType.inline.value,
        aws_update_tag,
    )


@timeit
def sync_roles(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM roles for account '%s'.", current_aws_account_id)
    data = get_role_list_data(boto3_session)
    load_roles(neo4j_session, data["Roles"], current_aws_account_id, aws_update_tag)

    sync_role_inline_policies(
        current_aws_account_id,
        boto3_session,
        data,
        neo4j_session,
        aws_update_tag,
    )

    sync_role_managed_policies(
        current_aws_account_id,
        boto3_session,
        data,
        neo4j_session,
        aws_update_tag,
    )

    run_cleanup_job(
        "aws_import_roles_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def sync_role_managed_policies(
    current_aws_account_id: str,
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Syncing IAM role managed policies for account '%s'.",
        current_aws_account_id,
    )
    managed_policy_data = get_role_managed_policy_data(boto3_session, data["Roles"])
    transformed_policy_data = transform_policy_data(
        managed_policy_data, PolicyType.managed.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        PolicyType.managed.value,
        aws_update_tag,
    )


def sync_role_inline_policies(
    current_aws_account_id: str,
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Syncing IAM role inline policies for account '%s'.",
        current_aws_account_id,
    )
    inline_policy_data = get_role_policy_data(boto3_session, data["Roles"])
    transformed_policy_data = transform_policy_data(
        inline_policy_data, PolicyType.inline.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        PolicyType.inline.value,
        aws_update_tag,
    )


@timeit
def sync_group_memberships(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info(
        "Syncing IAM group membership for account '%s'.",
        current_aws_account_id,
    )
    query = (
        "MATCH (group:AWSGroup)<-[:RESOURCE]-(:AWSAccount{id: $AWS_ACCOUNT_ID}) "
        "return group.name as name, group.arn as arn;"
    )
    groups = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id)
    groups_membership = {
        group["arn"]: get_group_membership_data(boto3_session, group["name"])
        for group in groups
    }
    load_group_memberships(neo4j_session, groups_membership, aws_update_tag)
    run_cleanup_job(
        "aws_import_groups_membership_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_user_access_keys(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info(
        "Syncing IAM user access keys for account '%s'.",
        current_aws_account_id,
    )
    query = (
        "MATCH (user:AWSUser)<-[:RESOURCE]-(:AWSAccount{id: $AWS_ACCOUNT_ID}) "
        "RETURN user.name as name, user.arn as arn"
    )
    for user in neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id):
        access_keys = get_account_access_key_data(boto3_session, user["name"])
        if access_keys:
            account_access_keys = {user["arn"]: access_keys}
            load_user_access_keys(neo4j_session, account_access_keys, aws_update_tag)
    run_cleanup_job(
        "aws_import_account_access_key_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM for account '%s'.", current_aws_account_id)
    # This module only syncs IAM information that is in use.
    # As such only policies that are attached to a user, role or group are synced
    sync_users(
        neo4j_session,
        boto3_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    sync_groups(
        neo4j_session,
        boto3_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    sync_roles(
        neo4j_session,
        boto3_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    sync_group_memberships(
        neo4j_session,
        boto3_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    sync_assumerole_relationships(
        neo4j_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    sync_user_access_keys(
        neo4j_session,
        boto3_session,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    run_cleanup_job(
        "aws_import_principals_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="AWSPrincipal",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )


@timeit
def get_account_from_arn(arn: str) -> str:
    # ARN documentation
    # https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html

    if not arn.startswith("arn:"):
        # must be a service principal arn, such as ec2.amazonaws.com
        return ""

    parts = arn.split(":")
    if len(parts) < 4:
        return ""
    else:
        return parts[4]
