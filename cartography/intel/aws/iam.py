import enum
import json
import logging
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.client.core.tx import read_list_of_values_tx
from cartography.graph.job import GraphJob
from cartography.intel.aws.permission_relationships import principal_allowed_on_resource
from cartography.models.aws.iam.access_key import AccountAccessKeySchema
from cartography.models.aws.iam.account_role import AWSAccountAWSRoleSchema
from cartography.models.aws.iam.federated_principal import AWSFederatedPrincipalSchema
from cartography.models.aws.iam.group import AWSGroupSchema
from cartography.models.aws.iam.inline_policy import AWSInlinePolicySchema
from cartography.models.aws.iam.managed_policy import AWSManagedPolicySchema
from cartography.models.aws.iam.policy_statement import AWSPolicyStatementSchema
from cartography.models.aws.iam.role import AWSRoleSchema
from cartography.models.aws.iam.root_principal import AWSRootPrincipalSchema
from cartography.models.aws.iam.service_principal import AWSServicePrincipalSchema
from cartography.models.aws.iam.sts_assumerole_allow import STSAssumeRoleAllowMatchLink
from cartography.models.aws.iam.user import AWSUserSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

# Overview of IAM in AWS
# https://aws.amazon.com/iam/


class PolicyType(enum.Enum):
    managed = "managed"
    inline = "inline"


TransformedRoleData = namedtuple(
    "TransformedRoleData",
    [
        "role_data",
        "federated_principals",
        "service_principals",
        "external_aws_accounts",
    ],
)

TransformedPolicyData = namedtuple(
    "TransformedPolicyData",
    [
        "managed_policies",
        "inline_policies",
        "statements_by_policy_id",
    ],
)


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
@aws_handle_regions
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
@aws_handle_regions
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
@aws_handle_regions
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
@aws_handle_regions
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
@aws_handle_regions
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
@aws_handle_regions
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
@aws_handle_regions
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
def get_user_access_keys_data(
    boto3_session: boto3.Session,
    users: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Get access key data for all users.
    Returns a dict mapping user ARN to list of access key data.
    """
    user_access_keys = {}

    for user in users:
        username = user["name"]
        user_arn = user["arn"]

        access_keys = get_account_access_key_data(boto3_session, username)
        if access_keys and "AccessKeyMetadata" in access_keys:
            user_access_keys[user_arn] = access_keys["AccessKeyMetadata"]
        else:
            user_access_keys[user_arn] = []

    return user_access_keys


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


@timeit
def get_group_memberships(
    boto3_session: boto3.Session, groups: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """
    Get membership data for all groups.
    Returns a dict mapping group ARN to list of user ARNs.
    """
    memberships = {}
    for group in groups:
        try:
            membership_data = get_group_membership_data(
                boto3_session, group["GroupName"]
            )
            if membership_data and "Users" in membership_data:
                memberships[group["Arn"]] = [
                    user["Arn"] for user in membership_data["Users"]
                ]
            else:
                memberships[group["Arn"]] = []
        except Exception:
            logger.warning(
                f"Could not get membership data for group {group['GroupName']}",
                exc_info=True,
            )
            memberships[group["Arn"]] = []

    return memberships


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
    results = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        get_policy_query,
        Arn=principal_arn,
    )
    policies = {r["policy_id"]: r["statements"] for r in results}
    return policies


def transform_users(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
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


def transform_groups(
    groups: list[dict[str, Any]], group_memberships: dict[str, list[str]]
) -> list[dict[str, Any]]:
    group_data = []
    for group in groups:
        group_record = {
            "arn": group["Arn"],
            "groupid": group["GroupId"],
            "name": group["GroupName"],
            "path": group["Path"],
            "createdate": str(group["CreateDate"]),
            "user_arns": group_memberships.get(group["Arn"], []),
        }
        group_data.append(group_record)

    return group_data


def transform_access_keys(
    user_access_keys: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    access_key_data = []
    for user_arn, access_keys in user_access_keys.items():
        for access_key in access_keys:
            if access_key.get("AccessKeyId"):
                access_key_record = {
                    "accesskeyid": access_key["AccessKeyId"],
                    "createdate": str(access_key["CreateDate"]),
                    "status": access_key["Status"],
                    "lastuseddate": str(access_key.get("LastUsedDate", "")),
                    "lastusedservice": access_key.get("LastUsedService", ""),
                    "lastusedregion": access_key.get("LastUsedRegion", ""),
                    "user_arn": user_arn,  # For the sub-resource relationship
                }
                access_key_data.append(access_key_record)

    return access_key_data


def transform_role_trust_policies(
    roles: list[dict[str, Any]], current_aws_account_id: str
) -> TransformedRoleData:
    """
    Processes AWS role assumption policy documents in the list_roles response.
    Returns a TransformedRoleData object containing the role data, federated principals, service principals, and external AWS accounts.
    """
    role_data: list[dict[str, Any]] = []
    federated_principals: list[dict[str, Any]] = []
    service_principals: list[dict[str, Any]] = []
    external_aws_accounts: list[dict[str, Any]] = []

    for role in roles:
        role_arn = role["Arn"]

        # List of principals of type "AWS" that this role trusts
        trusted_aws_principals = set()
        # Process each statement in the assume role policy document
        # TODO support conditions
        for statement in role["AssumeRolePolicyDocument"]["Statement"]:

            principal_entries = _parse_principal_entries(statement["Principal"])
            for principal_type, principal_arn in principal_entries:
                if principal_type == "Federated":
                    # Add this to list of federated nodes to create
                    account_id = get_account_from_arn(principal_arn)
                    federated_principals.append(
                        {
                            "arn": principal_arn,
                            "type": "Federated",
                            "other_account_id": (
                                account_id
                                if account_id != current_aws_account_id
                                else None
                            ),
                            "role_arn": role_arn,
                        }
                    )
                    trusted_aws_principals.add(principal_arn)
                elif principal_type == "Service":
                    # Add to the list of service nodes to create
                    service_principals.append(
                        {
                            "arn": principal_arn,
                            "type": "Service",
                        }
                    )
                    # Service principals are global so there is no account id.
                    trusted_aws_principals.add(principal_arn)
                elif principal_type == "AWS":
                    if "root" in principal_arn:
                        # The current principal trusts a root principal.

                        # First check if the root principal is in a different account than the current one.
                        # Add what we know about that account to the graph.
                        account_id = get_account_from_arn(principal_arn)
                        if account_id != current_aws_account_id:
                            external_aws_accounts.append({"id": account_id})
                    trusted_aws_principals.add(principal_arn)
                else:
                    # This should not happen but who knows.
                    logger.warning(f"Unknown principal type: {principal_type}")

        role_record = {
            "arn": role["Arn"],
            "roleid": role["RoleId"],
            "name": role["RoleName"],
            "path": role["Path"],
            "createdate": str(role["CreateDate"]),
            "trusted_aws_principals": list(trusted_aws_principals),
            "account_id": get_account_from_arn(role["Arn"]),
        }
        role_data.append(role_record)

    return TransformedRoleData(
        role_data=role_data,
        federated_principals=federated_principals,
        service_principals=service_principals,
        external_aws_accounts=external_aws_accounts,
    )


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
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    groups: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSGroupSchema(),
        groups,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_access_keys(
    neo4j_session: neo4j.Session,
    access_keys: List[Dict],
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    load(
        neo4j_session,
        AccountAccessKeySchema(),
        access_keys,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
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
    WHERE NOT source:AWSRootPrincipal
    AND NOT source:AWSServicePrincipal
    AND NOT source:AWSFederatedPrincipal
    RETURN target.arn AS target_arn, source.arn AS source_arn
    """
    results = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query_potential_matches,
        AccountId=current_aws_account_id,
    )

    # Filter potential matches to only those where the source principal has sts:AssumeRole permission
    valid_matches = []
    for result in results:
        source_arn = result["source_arn"]
        target_arn = result["target_arn"]
        policies = get_policies_for_principal(neo4j_session, source_arn)
        if principal_allowed_on_resource(policies, target_arn, ["sts:AssumeRole"]):
            valid_matches.append(
                {
                    "source_arn": source_arn,
                    "target_arn": target_arn,
                }
            )

    load_matchlinks(
        neo4j_session,
        STSAssumeRoleAllowMatchLink(),
        valid_matches,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_account_id,
    )

    GraphJob.from_matchlink(
        STSAssumeRoleAllowMatchLink(),
        sub_resource_label="AWSAccount",
        sub_resource_id=current_aws_account_id,
        update_tag=aws_update_tag,
    ).run(neo4j_session)


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
    policy_map: dict[str, dict[str, Any]], policy_type: str
) -> TransformedPolicyData:
    """
    Processes AWS IAM policy documents. Returns a TransformedPolicyData object containing the managed policies, inline policies, and statements by policy id -- all ready to be loaded to the graph.
    """
    # First pass: collect all policies and their principals
    policy_to_principals: dict[str, set[str]] = {}
    policy_to_statements: dict[str, list[dict[str, Any]]] = {}
    policy_to_name: dict[str, str] = {}

    for principal_arn, policy_statement_map in policy_map.items():
        for policy_key, statements in policy_statement_map.items():
            policy_id = (
                transform_policy_id(principal_arn, policy_type, policy_key)
                if policy_type == PolicyType.inline.value
                else policy_key
            )
            policy_name = (
                policy_key
                if policy_type == PolicyType.inline.value
                else get_policy_name_from_arn(policy_key)
            )
            # Map policy id to the principal arns that have it
            if policy_id not in policy_to_principals:
                policy_to_principals[policy_id] = set()
            policy_to_principals[policy_id].add(principal_arn)

            # Map policy id to policy name
            policy_to_name[policy_id] = policy_name

            # Transform and store statements
            transformed_statements = _transform_policy_statements(
                statements,
                policy_id,
            )
            policy_to_statements[policy_id] = transformed_statements

    # Second pass: create consolidated policy data
    managed_policy_data = []
    inline_policy_data = []

    for policy_id, principal_arns in policy_to_principals.items():
        policy_name = policy_to_name[policy_id]

        policy_data = {
            "id": policy_id,
            "name": policy_name,
            "type": policy_type,
            # AWS inline policies don't have arns
            "arn": policy_id if policy_type == PolicyType.managed.value else None,
            "principal_arns": list(principal_arns),
        }

        if policy_type == PolicyType.inline.value:
            inline_policy_data.append(policy_data)
        elif policy_type == PolicyType.managed.value:
            managed_policy_data.append(policy_data)
        else:
            # This really should never happen so just explicitly having a `pass` here.
            pass

    return TransformedPolicyData(
        managed_policies=managed_policy_data,
        inline_policies=inline_policy_data,
        statements_by_policy_id=policy_to_statements,
    )


def transform_policy_id(principal_arn: str, policy_type: str, name: str) -> str:
    return f"{principal_arn}/{policy_type}_policy/{name}"


def _load_policy(
    neo4j_session: neo4j.Session,
    managed_policy_data: list[dict[str, Any]],
    inline_policy_data: list[dict[str, Any]],
    account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSManagedPolicySchema(),
        managed_policy_data,
        lastupdated=aws_update_tag,
    )
    load(
        neo4j_session,
        AWSInlinePolicySchema(),
        inline_policy_data,
        lastupdated=aws_update_tag,
        AWS_ID=account_id,
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
        POLICY_ID=statements[0]["policy_id"],
    )


@timeit
def _load_policy_statements(
    neo4j_session: neo4j.Session,
    policy_statements: dict[str, list[dict[str, Any]]],
    aws_update_tag: int,
) -> None:
    for policy_id, statements in policy_statements.items():
        load(
            neo4j_session,
            AWSPolicyStatementSchema(),
            statements,
            lastupdated=aws_update_tag,
            POLICY_ID=policy_id,
        )


@timeit
def load_policy_data(
    neo4j_session: neo4j.Session,
    transformed_policy_data: TransformedPolicyData,
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    _load_policy(
        neo4j_session,
        transformed_policy_data.managed_policies,
        transformed_policy_data.inline_policies,
        current_aws_account_id,
        aws_update_tag,
    )

    _load_policy_statements(
        neo4j_session,
        transformed_policy_data.statements_by_policy_id,
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

    sync_user_inline_policies(
        boto3_session, data, neo4j_session, aws_update_tag, current_aws_account_id
    )

    sync_user_managed_policies(
        boto3_session, data, neo4j_session, aws_update_tag, current_aws_account_id
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
        "Syncing IAM user access keys for account '%s'.", current_aws_account_id
    )

    # Query the graph for users instead of making another AWS API call
    query = (
        "MATCH (user:AWSUser)<-[:RESOURCE]-(:AWSAccount{id: $AWS_ID}) "
        "RETURN user.name as name, user.arn as arn"
    )
    users = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        query,
        AWS_ID=current_aws_account_id,
    )

    user_access_keys = get_user_access_keys_data(boto3_session, users)
    access_key_data = transform_access_keys(user_access_keys)
    load_access_keys(
        neo4j_session, access_key_data, aws_update_tag, current_aws_account_id
    )
    GraphJob.from_node_schema(AccountAccessKeySchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_user_managed_policies(
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    managed_policy_data = get_user_managed_policy_data(boto3_session, data["Users"])
    transformed_policy_data = transform_policy_data(
        managed_policy_data, PolicyType.managed.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        aws_update_tag,
        current_aws_account_id,
    )


@timeit
def sync_user_inline_policies(
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    policy_data = get_user_policy_data(boto3_session, data["Users"])
    transformed_policy_data = transform_policy_data(
        policy_data, PolicyType.inline.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        aws_update_tag,
        current_aws_account_id,
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
    group_memberships = get_group_memberships(boto3_session, data["Groups"])
    group_data = transform_groups(data["Groups"], group_memberships)
    load_groups(neo4j_session, group_data, current_aws_account_id, aws_update_tag)

    sync_groups_inline_policies(
        boto3_session, data, neo4j_session, aws_update_tag, current_aws_account_id
    )

    sync_group_managed_policies(
        boto3_session, data, neo4j_session, aws_update_tag, current_aws_account_id
    )


def sync_group_managed_policies(
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    managed_policy_data = get_group_managed_policy_data(boto3_session, data["Groups"])
    transformed_policy_data = transform_policy_data(
        managed_policy_data, PolicyType.managed.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        aws_update_tag,
        current_aws_account_id,
    )


def sync_groups_inline_policies(
    boto3_session: boto3.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
    current_aws_account_id: str,
) -> None:
    policy_data = get_group_policy_data(boto3_session, data["Groups"])
    transformed_policy_data = transform_policy_data(
        policy_data, PolicyType.inline.value
    )
    load_policy_data(
        neo4j_session,
        transformed_policy_data,
        aws_update_tag,
        current_aws_account_id,
    )


def load_external_aws_accounts(
    neo4j_session: neo4j.Session,
    external_aws_accounts: list[dict[str, Any]],
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSAccountAWSRoleSchema(),
        external_aws_accounts,
        lastupdated=aws_update_tag,
    )
    # Ensure that the root principal exists for each external account.
    for account in external_aws_accounts:
        sync_root_principal(
            neo4j_session,
            account["id"],
            aws_update_tag,
        )


@timeit
def load_service_principals(
    neo4j_session: neo4j.Session,
    service_principals: list[dict[str, Any]],
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSServicePrincipalSchema(),
        service_principals,
        lastupdated=aws_update_tag,
    )


@timeit
def load_role_data(
    neo4j_session: neo4j.Session,
    role_list: list[dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    # Note that the account_id is set in the transform_roles function instead of from the `AWS_ID` kwarg like in other modules
    # because this can create root principals from other accounts based on data from the assume role policy document.
    load(
        neo4j_session,
        AWSRoleSchema(),
        role_list,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_federated_principals(
    neo4j_session: neo4j.Session,
    federated_principals: list[dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSFederatedPrincipalSchema(),
        federated_principals,
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def sync_role_assumptions(
    neo4j_session: neo4j.Session,
    data: dict[str, Any],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    transformed = transform_role_trust_policies(data["Roles"], current_aws_account_id)

    # Order matters here.
    # External accounts come first because they need to be created before the roles that trust them.
    load_external_aws_accounts(
        neo4j_session, transformed.external_aws_accounts, aws_update_tag
    )
    # Service principals e.g. arn = "ec2.amazonaws.com" come next because they're global
    load_service_principals(
        neo4j_session, transformed.service_principals, aws_update_tag
    )
    load_federated_principals(
        neo4j_session,
        transformed.federated_principals,
        current_aws_account_id,
        aws_update_tag,
    )
    load_role_data(
        neo4j_session, transformed.role_data, current_aws_account_id, aws_update_tag
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

    sync_role_assumptions(neo4j_session, data, current_aws_account_id, aws_update_tag)

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
        aws_update_tag,
        current_aws_account_id,
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
        aws_update_tag,
        current_aws_account_id,
    )


def _get_policies_in_current_account(
    neo4j_session: neo4j.Session, current_aws_account_id: str
) -> list[str]:
    query = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(p:AWSPolicy)
    RETURN p.id
    """
    return [
        str(policy_id)
        for policy_id in neo4j_session.execute_read(
            read_list_of_values_tx,
            query,
            AWS_ID=current_aws_account_id,
        )
    ]


def _get_principals_with_pols_in_current_account(
    neo4j_session: neo4j.Session, current_aws_account_id: str
) -> list[str]:
    query = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(p:AWSPrincipal)
    WHERE (p)-[:POLICY]->(:AWSPolicy)
    RETURN p.id
    """
    return [
        str(principal_id)
        for principal_id in neo4j_session.execute_read(
            read_list_of_values_tx,
            query,
            AWS_ID=current_aws_account_id,
        )
    ]


@timeit
def cleanup_iam(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    # List all policies in the current account
    policy_ids = _get_policies_in_current_account(
        neo4j_session, common_job_parameters["AWS_ID"]
    )

    # for each policy id, run the cleanup job for the policy statements, passing the policy id as a kwarg.
    for policy_id in policy_ids:
        GraphJob.from_node_schema(
            AWSPolicyStatementSchema(),
            {**common_job_parameters, "POLICY_ID": policy_id},
        ).run(
            neo4j_session,
        )

    # Next, clean up the policies
    # Note that managed policies don't have a sub resource relationship. This means that we will only clean up
    # stale relationships and not stale AWSManagedPolicy nodes. This is because AWSManagedPolicy nodes are global
    # to AWS and it is possible for them to be shared across accounts, so if we cleaned up an AWSManagedPolicy node
    # for one account, it would be erroneously deleted for all accounts. Instead, we just clean up the relationships.
    GraphJob.from_node_schema(AWSManagedPolicySchema(), common_job_parameters).run(
        neo4j_session
    )

    # Inline policies are simpler in that they are scoped to a single principal and therefore attached to that
    # principal's account. This means that this operation will clean up stale AWSInlinePolicy nodes.
    GraphJob.from_node_schema(AWSInlinePolicySchema(), common_job_parameters).run(
        neo4j_session
    )

    # Clean up roles before federated and service principals
    GraphJob.from_node_schema(AWSRoleSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(AWSFederatedPrincipalSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AWSServicePrincipalSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AWSUserSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(AWSGroupSchema(), common_job_parameters).run(
        neo4j_session
    )


def sync_root_principal(
    neo4j_session: neo4j.Session, current_aws_account_id: str, aws_update_tag: int
) -> None:
    """
    In the current account, create a node for the AWS root principal "arn:aws:iam::<account_id>:root".

    If a role X trusts the root principal in an account A, then any other role Y in A can assume X.

    Note that this is _not_ the same as the AWS root user. The root principal doesn't show up in any
    APIs except for assumerole trust policies.
    """
    load(
        neo4j_session,
        AWSRootPrincipalSchema(),
        [{"arn": f"arn:aws:iam::{current_aws_account_id}:root"}],
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
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
    sync_root_principal(
        neo4j_session,
        current_aws_account_id,
        update_tag,
    )
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
    cleanup_iam(neo4j_session, common_job_parameters)
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
