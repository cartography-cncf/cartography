import enum
import json
import logging
import time
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import neo4j
from botocore.exceptions import ClientError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.permission_relationships import parse_statement_node
from cartography.intel.aws.permission_relationships import principal_allowed_on_resource
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()

# Overview of IAM in AWS
# https://aws.amazon.com/iam/


class PolicyType(enum.Enum):
    managed = "managed"
    inline = "inline"


def get_policy_name_from_arn(arn: str) -> str:
    return arn.split("/")[-1]


@timeit
def _is_common_exception(e: Exception, item: str) -> bool:
    error_msg = "Failed to retrieve IAM details"
    if "AccessDenied" in e.args[0]:
        logger.warning(f"{error_msg} for {item} - Access Denied")
        return True
    elif "NoSuchEntityException" in e.args[0]:
        logger.warning(f"{error_msg} for {item} - NoSuchEntityException")
        return True
    elif "EndpointConnectionError" in e.args[0]:
        logger.warning(f"{error_msg} for {item} - EndpointConnectionError")
        return True
    elif "InvalidToken" in e.args[0]:
        logger.warning(f"{error_msg} for {item} - InvalidToken")
        return True
    elif "IllegalLocationConstraintException" in e.args[0]:
        logger.warning(f"{error_msg} for {item} - IllegalLocationConstraintException")
        return True
    return False


@timeit
def get_group_policies(boto3_session: boto3.session.Session, group_name: str) -> Dict:
    client = boto3_session.client("iam")
    paginator = client.get_paginator("list_group_policies")
    policy_names: List[Dict] = []
    for page in paginator.paginate(GroupName=group_name):
        policy_names.extend(page["PolicyNames"])
    return {"PolicyNames": policy_names}


@timeit
def get_group_policy_info(
    boto3_session: boto3.session.Session,
    group_name: str,
    policy_name: str,
) -> Any:
    client = boto3_session.client("iam")
    return client.get_group_policy(GroupName=group_name, PolicyName=policy_name)


@timeit
def get_group_membership_data(boto3_session: boto3.session.Session, group_name: str) -> Dict:
    client = boto3_session.client("iam")
    try:
        memberships = client.get_group(GroupName=group_name)
        return memberships

    except ClientError as e:
        if _is_common_exception(e, group_name):
            pass
        else:
            logger.warning("client.get_group(GroupName='%s') failed with NoSuchEntityException; skipping.", group_name)
        return {}


@timeit
def get_group_policy_data(boto3_session: boto3.session.Session, group_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for group in group_list:
        name = group["GroupName"]
        arn = group["Arn"]
        resource_group = resource_client.Group(name)
        policies[arn] = policies[arn] = {p.name: p.policy_document["Statement"] for p in resource_group.policies.all()}
    return policies


@timeit
def get_group_managed_policy_data(boto3_session: boto3.session.Session, group_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for group in group_list:
        name = group["GroupName"]
        group_arn = group["Arn"]
        resource_group = resource_client.Group(name)
        policies[group_arn] = {
            p.policy_name: p.default_version.document["Statement"] for p in resource_group.attached_policies.all()
        }
    return policies


@timeit
def get_user_policy_data(boto3_session: boto3.session.Session, user_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for user in user_list:
        name = user["UserName"]
        arn = user["Arn"]
        resource_user = resource_client.User(name)
        try:
            policies[arn] = {p.name: p.policy_document["Statement"] for p in resource_user.policies.all()}

        except ClientError as e:
            if _is_common_exception(e, name):
                pass
            else:
                logger.warning(
                    f"Could not get policies for user {name} due to NoSuchEntityException; skipping.",
                )
    return policies


@timeit
def get_user_managed_policy_data(boto3_session: boto3.session.Session, user_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for user in user_list:
        name = user["UserName"]
        user_arn = user["Arn"]
        resource_user = resource_client.User(name)
        try:
            policies[user_arn] = {
                p.policy_name: p.default_version.document["Statement"] for p in resource_user.attached_policies.all()
            }

        except ClientError as e:
            if _is_common_exception(e, name):
                pass
            else:
                logger.warning(
                    f"Could not get policies for user {name} due to NoSuchEntityException; skipping.",
                )
    return policies


@timeit
def get_role_policy_data(boto3_session: boto3.session.Session, role_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for role in role_list:
        name = role["RoleName"]
        arn = role["Arn"]
        resource_role = resource_client.Role(name)
        try:
            policies[arn] = {p.name: p.policy_document["Statement"] for p in resource_role.policies.all()}

        except ClientError as e:
            if _is_common_exception(e, name):
                pass
            else:
                logger.warning(
                    f"Could not get policies for role {name} due to NoSuchEntityException; skipping.",
                )
    return policies


@timeit
def get_role_managed_policy_data(boto3_session: boto3.session.Session, role_list: List[Dict]) -> Dict:
    resource_client = boto3_session.resource("iam")
    policies = {}
    for role in role_list:
        name = role["RoleName"]
        role_arn = role["Arn"]
        resource_role = resource_client.Role(name)
        try:
            policies[role_arn] = {
                p.policy_name: p.default_version.document["Statement"] for p in resource_role.attached_policies.all()
            }
        except ClientError as e:
            if _is_common_exception(e, name):
                pass
            else:
                logger.warning(
                    f"Could not get policies for role {name} due to NoSuchEntityException; skipping.",
                )
    return policies


@timeit
def get_role_tags(boto3_session: boto3.session.Session) -> List[Dict]:
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
def get_user_list_data(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client("iam")

    paginator = client.get_paginator("list_users")
    users: List[Dict] = []
    for page in paginator.paginate():
        users.extend(page["Users"])
    return {"Users": users}


@timeit
def get_policies_list_data(boto3_session: boto3.session.Session) -> List[Dict]:
    client = boto3_session.client("iam")

    paginator = client.get_paginator("list_policies")
    policies: List[Dict] = []
    for page in paginator.paginate():
        policies.extend(page["Policies"])
    return policies


@timeit
def transform_policies_data(current_aws_account_id: str, policies: List[Dict]) -> List[Dict]:
    for policy in policies:
        policy["id"] = transform_policy_id(current_aws_account_id, PolicyType.managed.value, policy.get("PolicyName"))
    return policies


@timeit
def transform_users_data(boto3_session: boto3.session.Session, users: List[Dict]) -> Dict:
    client = boto3_session.client("iam")
    for user in users:
        try:
            client.get_login_profile(UserName=user["UserName"])
            user["consoleLoginEnabled"] = True
        except client.exceptions.NoSuchEntityException:
            user["consoleLoginEnabled"] = False
        except Exception:
            user["consoleLoginEnabled"] = False
        try:
            mfa_devices = client.list_mfa_devices(UserName=user["UserName"])
            if len(mfa_devices.get("MFADevices", [])) > 0:
                user["MFAEnabled"] = True
            else:
                user["MFAEnabled"] = False
        except client.exceptions.NoSuchEntityException:
            user["MFAEnabled"] = False
        except Exception:
            user["MFAEnabled"] = False
    return {"Users": users}


@timeit
def get_group_list_data(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client("iam")
    paginator = client.get_paginator("list_groups")
    groups: List[Dict] = []
    for page in paginator.paginate():
        groups.extend(page["Groups"])
    return {"Groups": groups}


@timeit
def get_role_list_data(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client("iam")
    paginator = client.get_paginator("list_roles")
    roles: List[Dict] = []
    for page in paginator.paginate():
        roles.extend(page["Roles"])

    service_role_types = ["/aws-service-role/", "/service-role/", "/aws-reserved/"]
    sso_reserved_types = ["/aws-reserved/sso.amazonaws.com/"]
    for role in roles:
        try:
            role_data = client.get_role(RoleName=role.get("RoleName")).get("Role")
            role["RoleLastUsed"] = role_data.get("RoleLastUsed")
            role["type"] = "custom"

            if any(service_role_type in role_data.get("Path", "") for service_role_type in service_role_types):
                # Skip this roles from IAM-JIT, because we can't edit the trust policy for these types of roles
                role["isServiceRole"] = True
                role["type"] = "predefined"

            if any(sso_reserved_type in role_data.get("Path", "") for sso_reserved_type in sso_reserved_types):
                # Skip this roles from IAM-JIT, because we can't edit the trust policy for these types of roles
                role["isSSOReservedRole"] = True
                role["type"] = "predefined"

        except Exception as e:
            logger.warning(f"Failed to get role info. {e}")
    return {"Roles": roles}


@timeit
def get_external_access_roles(boto3_session: boto3.session.Session, common_job_parameters: Dict) -> List[Dict]:
    try:
        analyzer_client = boto3_session.client("accessanalyzer", region_name=common_job_parameters.get("DEFAULT_REGION", None))
        # AWS allow to create only one analyzer per account per region with type (ACCOUNT, ORGANIZATION, ACCOUNT_UNUSED_ACCESS, and ORGANIZTAION_UNUSED_ACCESS) thats why uses analyzers_list index 0
        analyzers_list = analyzer_client.list_analyzers(type="ACCOUNT").get("analyzers", [])
        findings: List = []
        if analyzers_list:
            paginator = analyzer_client.get_paginator("list_findings_v2")
            for page in paginator.paginate(
                analyzerArn=analyzers_list[0].get("arn"),
                filter={"resourceType": {"eq": ["AWS::IAM::Role"]}},
            ):
                findings.extend(page.get("findings", []))
            return findings
        else:
            analyzer_client.create_analyzer(
                analyzerName="cdx_analyzer",
                type="ACCOUNT",
                tags={"owner": "cloudanix", "project": "iam-entitlements-analyzer"},
            )
            return findings
    except (ClientError, Exception) as e:
        logger.warning(f"Failed to get external roles. {e}")
        return []


@timeit
def transform_roles(
    boto3_session: boto3.session.Session,
    roles: List[Dict],
    external_access_roles: List[Dict],
    common_job_parameters: Dict,
) -> Dict:
    external_access_roles_arn_list = [d["resource"] for d in external_access_roles if "resource" in d]

    try:
        client = boto3_session.client("organizations")
        response = client.list_accounts()
        internal_accounts = [account["Id"] for account in response["Accounts"]]
    except Exception:
        internal_accounts = []

    for role in roles:
        ExternalAccountPrincipals = []
        if role["Arn"] in external_access_roles_arn_list:
            for statement in role["AssumeRolePolicyDocument"]["Statement"]:
                principal_entries = _parse_principal_entries(statement["Principal"])
                for principal_type, principal in principal_entries:
                    internal_principal = False

                    try:
                        account_id = principal.split(":")[4]
                    except Exception:
                        account_id = principal

                    if account_id == common_job_parameters["AWS_ACCOUNT_ID"]:
                        continue

                    if internal_accounts and account_id in internal_accounts:
                        internal_principal = True

                    if (
                        common_job_parameters["AWS_INTERNAL_ACCOUNTS"] and
                        account_id in common_job_parameters["AWS_INTERNAL_ACCOUNTS"]
                    ):
                        internal_principal = True

                    if not internal_principal:
                        ExternalAccountPrincipals.append(
                            {
                                "access_type": "ThirdParty",
                                "account_id": account_id,
                                "principal": principal,
                            },
                        )
                    else:
                        ExternalAccountPrincipals.append(
                            {
                                "access_type": "CrossAccount",
                                "account_id": account_id,
                                "principal": principal,
                            },
                        )

        role["ExternalAccountPrincipals"] = ExternalAccountPrincipals

    return {"Roles": roles}


@timeit
def get_account_access_key_data(boto3_session: boto3.session.Session, username: str) -> Dict:
    client = boto3_session.client("iam")
    # NOTE we can get away without using a paginator here because users are limited to two access keys
    access_keys: Dict = {}
    try:
        access_keys = client.list_access_keys(UserName=username)
        for access_key in access_keys["AccessKeyMetadata"]:
            last_used = client.get_access_key_last_used(AccessKeyId=access_key.get("AccessKeyId"))
            access_key["LastUsedDate"] = last_used.get("AccessKeyLastUsed", {}).get("LastUsedDate")
            access_key["CreateDate"] = access_key.get("CreateDate")

            current_date = datetime.now(timezone.utc)
            day_difference = (current_date - access_key.get("CreateDate")).days
            access_key["KeyAge"] = f"{day_difference} days"

    except ClientError as e:
        if _is_common_exception(e, username):
            pass
        else:
            logger.warning(
                f"Could not get access key for user {username} due to NoSuchEntityException; skipping.",
            )
    return access_keys


@timeit
def load_users(
    neo4j_session: neo4j.Session,
    users: List[Dict],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_user = """
    MERGE (unode:AWSUser{arn: $ARN})
    ON CREATE SET unode:AWSPrincipal, unode.userid = $USERID, unode.firstseen = timestamp(),
    unode.consolelink = $consolelink,
    unode.createdate = $CREATE_DATE
    SET unode.name = $USERNAME, unode.user_name = $USERNAME,
    unode.path = $PATH, unode.passwordlastused = $PASSWORD_LASTUSED,
    unode.region = $region,
    unode.consoleloginenabled = $CONSOLELOGINENABLED,
    unode.mfaenabled = $MFAENABLED,
    unode.lastupdated = $aws_update_tag
    WITH unode
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(unode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    logger.info(f"Loading {len(users)} IAM users.")
    for user in users:
        neo4j_session.run(
            ingest_user,
            ARN=user["Arn"],
            consolelink=aws_console_link.get_console_link(arn=user["Arn"]),
            USERID=user["UserId"],
            CREATE_DATE=str(user["CreateDate"]),
            USERNAME=user["UserName"],
            PATH=user["Path"],
            CONSOLELOGINENABLED=user.get("consoleLoginEnabled", False),
            MFAENABLED=user.get("MFAEnabled", False),
            PASSWORD_LASTUSED=str(user.get("PasswordLastUsed", "")),
            AWS_ACCOUNT_ID=current_aws_account_id,
            region="global",
            aws_update_tag=aws_update_tag,
        )


@timeit
def load_policies_for_account(
    neo4j_session: neo4j.Session,
    policies_list: List[Dict],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    neo4j_session.write_transaction(_load_policies_for_account_tx, policies_list, current_aws_account_id, update_tag)


@timeit
def _load_policies_for_account_tx(
    tx: neo4j.Transaction,
    policies_list: List[Dict],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_users = """
    UNWIND $policies_list AS policy
        MERGE (p:AWSPolicy{id: policy.id})
        ON CREATE SET
            p.firstseen = timestamp()
        SET
            p.name = policy.PolicyName,
            p.type = $policy_type,
            p.policy_id = policy.PolicyId,
            p.arn = policy.Arn,
            p.default_version_id = policy.DefaultVersionId,
            p.is_attachable = policy.IsAttachable,
            p.region = $region,
            p.lastupdated = $update_tag
        WITH p
            MATCH (i:AWSAccount{id: $AWS_ACCOUNT_ID})
            MERGE (i)-[r:RESOURCE]->(p)
            ON CREATE SET
                r.firstseen = timestamp()
            SET
                r.lastupdated = $update_tag
    """

    tx.run(
        ingest_users,
        policies_list=policies_list,
        AWS_ACCOUNT_ID=current_aws_account_id,
        policy_type=PolicyType.managed.value,
        region="global",
        update_tag=update_tag,
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
    SET gnode:AWSPrincipal, gnode.name = $GROUP_NAME, gnode.path = $PATH,
    gnode.region = $region,
    gnode.consolelink = $consolelink,
    gnode.lastupdated = $aws_update_tag
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
            consolelink=aws_console_link.get_console_link(arn=group["Arn"]),
            GROUP_ID=group["GroupId"],
            CREATE_DATE=str(group["CreateDate"]),
            GROUP_NAME=group["GroupName"],
            PATH=group["Path"],
            region="global",
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
    MERGE (rnode:AWSRole{arn: $Arn})
    ON CREATE SET rnode:AWSPrincipal, rnode.roleid = $RoleId, rnode.firstseen = timestamp(),
    rnode.region = $region,
    rnode.consolelink = $consolelink,
    rnode.createdate = $CreateDate
    SET rnode.name = $RoleName, rnode.path = $Path,
    rnode.lastuseddate = $LastUsedDate, rnode.lastusedregion = $LastUsedRegion,
    rnode.is_service_role = $IsServiceRole,
    rnode.is_sso_reserved_role = $IsSSOReservedRole,
    rnode.type = $Type
    SET rnode.lastupdated = $aws_update_tag
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

    ingest_external_account_principals = """
    MERGE (epnode:AWSExternalPrincipal{principal: $principal})
    ON CREATE SET epnode.firstseen = timestamp()
    SET epnode.lastupdated = $aws_update_tag,
    epnode.access_type = $AccessType,
    epnode.account_id = $AccountId
    WITH epnode
    MATCH (role:AWSRole{arn: $RoleArn})
    MERGE (role)-[r:TRUSTS_AWS_PRINCIPAL]->(epnode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    # TODO support conditions
    logger.info(f"Loading {len(roles)} IAM roles to the graph.")
    for role in roles:
        neo4j_session.run(
            ingest_role,
            Arn=role["Arn"],
            consolelink=aws_console_link.get_console_link(arn=role["Arn"]),
            RoleId=role.get("RoleId", None),
            CreateDate=str(role["CreateDate"]),
            RoleName=role["RoleName"],
            Path=role["Path"],
            IsServiceRole=role.get("isServiceRole", False),
            IsSSOReservedRole=role.get("isSSOReservedRole", False),
            Type=role.get("type", None),
            region="global",
            LastUsedDate=role["RoleLastUsed"].get("LastUsedDate") if "RoleLastUsed" in role else None,
            LastUsedRegion=role["RoleLastUsed"].get("Region") if "RoleLastUsed" in role else None,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )

        for external_principal in role["ExternalAccountPrincipals"]:
            neo4j_session.run(
                ingest_external_account_principals,
                principal=external_principal.get("principal"),
                AccessType=external_principal.get("access_type"),
                AccountId=external_principal.get("account_id"),
                RoleArn=role["Arn"],
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


@timeit
def load_group_memberships(neo4j_session: neo4j.Session, group_memberships: Dict, aws_update_tag: int) -> None:
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
def get_policies_for_principal(neo4j_session: neo4j.Session, principal_arn: str) -> Dict:
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
    aws_update_tag: str,
    common_job_parameters: Dict,
) -> None:
    # Must be called after load_role
    # Computes and syncs the STS_ASSUME_ROLE allow relationship
    logger.info("Syncing assume role mappings for account '%s'.", current_aws_account_id)
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
    consolelink: str,
) -> None:
    # Ref to rotatedate - https://aws.amazon.com/blogs/security/how-to-rotate-access-keys-for-iam-users/
    # To rotate key there is no option in aws. we need to create new and delete existing key that's why rotatedate same as createdate
    # TODO change the node label to reflect that this is a user access key, not an account access key
    ingest_account_key = """
    MATCH (user:AWSUser{arn: $ARN})
    WITH user
    MERGE (key:AccountAccessKey{accesskeyid: $AccessKeyId})
    ON CREATE SET key.firstseen = timestamp(),
    key.region = $region,
    key.createdate = $CreateDate,
    key.rotatedate = $CreateDate,
    key.consolelink = $consolelink
    SET key.status = $Status,
    key.keyage = $KeyAge,
    key.lastuseddate = $LastUsedDate,
    key.lastupdated = $aws_update_tag
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
                    consolelink=consolelink,
                    ARN=arn,
                    AccessKeyId=key["AccessKeyId"],
                    LastUsedDate=str(key.get("LastUsedDate", "")),
                    CreateDate=str(key.get("CreateDate", "")),
                    KeyAge=str(key.get("KeyAge", "")),
                    Status=key["Status"],
                    region="global",
                    aws_update_tag=aws_update_tag,
                )


def ensure_list(obj: Any) -> List[Any]:
    if not isinstance(obj, list):
        obj = [obj]
    return obj


def _transform_policy_statements(statements: Any, policy_id: str) -> List[Dict]:
    count = 1
    if not isinstance(statements, list):
        statements = [statements]
    for stmt in statements:
        if "Sid" not in stmt:
            statement_id = count
            count += 1
        else:
            statement_id = stmt["Sid"]
        stmt["id"] = f"{policy_id}/statement/{statement_id}"
        if "Resource" in stmt:
            stmt["Resource"] = ensure_list(stmt["Resource"])
        if "Action" in stmt:
            stmt["Action"] = ensure_list(stmt["Action"])
        if "NotAction" in stmt:
            stmt["NotAction"] = ensure_list(stmt["NotAction"])
        if "NotResource" in stmt:
            stmt["NotResource"] = ensure_list(stmt["NotResource"])
        if "Condition" in stmt:
            stmt["Condition"] = json.dumps(ensure_list(stmt["Condition"]))
    return statements


def transform_policy_data(policy_map: Dict, policy_type: str, current_aws_account_id: str) -> None:
    for principal_arn, policy_statement_map in policy_map.items():
        logger.debug(f"Transforming IAM {policy_type} policies for principal {principal_arn}")
        for policy_key, statements in policy_statement_map.items():
            policy_id = transform_policy_id(
                current_aws_account_id,
                policy_type,
                policy_key,
            )
            policy_statement_map[policy_key] = _transform_policy_statements(statements, policy_id)


def transform_policy_id(current_aws_account_id: str, policy_type: str, name: str) -> str:
    return f"{current_aws_account_id}/{policy_type}_policy/{name}"


def _load_policy_tx(
    tx: neo4j.Transaction,
    policy_id: str,
    policy_name: str,
    policy_type: str,
    principal_arn: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_policy = """
    MERGE (policy:AWSPolicy{id: $PolicyId})
    ON CREATE SET
    policy.firstseen = timestamp(),
    policy.type = $PolicyType,
    policy.region = $region,
    policy.name = $PolicyName,
    policy.arn = $PolicyArn,
    policy.consolelink = $consolelink
    SET policy.lastupdated = $aws_update_tag
    WITH policy
    MATCH (principal:AWSPrincipal{arn: $PrincipalArn})
    MERGE (policy) <-[r:POLICY]-(principal)
    SET r.lastupdated = $aws_update_tag
    """
    if policy_type == PolicyType.managed.value:
        ingest_policy = """
        MERGE (policy:AWSPolicy{id: $PolicyId})
        ON CREATE SET
        policy.firstseen = timestamp()
        SET
        policy.lastupdated = $aws_update_tag
        WITH policy
        MATCH (principal:AWSPrincipal{arn: $PrincipalArn})
        MERGE (policy) <-[r:POLICY]-(principal)
        SET r.lastupdated = $aws_update_tag
        """

    policy = policy_name.split("/")[-1]
    policy_arn = f"arn:aws:iam::{current_aws_account_id}:policy/{policy}"
    consolelink = aws_console_link.get_console_link(arn=policy_arn)

    tx.run(
        ingest_policy,
        PolicyId=policy_id,
        PolicyName=policy_name,
        PolicyType=policy_type,
        PrincipalArn=principal_arn,
        consolelink=consolelink,
        PolicyArn=policy_arn,
        region="global",
        aws_update_tag=aws_update_tag,
    )

    ingest_sso_policy = """
    MERGE (policy:AWSPolicy{id: $PolicyId})
    ON CREATE SET
    policy.firstseen = timestamp(),
    policy.type = $PolicyType,
    policy.region = $region,
    policy.name = $PolicyName,
    policy.arn = $PolicyArn,
    policy.consolelink = $consolelink
    SET policy.lastupdated = $aws_update_tag
    WITH policy
    MATCH (principal:AWSPrincipal{id: $PrincipalArn})
    MERGE (policy) <-[r:POLICY]-(principal)
    SET r.lastupdated = $aws_update_tag
    """
    if policy_type == PolicyType.managed.value:
        ingest_sso_policy = """
        MERGE (policy:AWSPolicy{id: $PolicyId})
        ON CREATE SET
        policy.firstseen = timestamp()
        SET
        policy.lastupdated = $aws_update_tag
        WITH policy
        MATCH (principal:AWSPrincipal{id: $PrincipalArn})
        MERGE (policy) <-[r:POLICY]-(principal)
        SET r.lastupdated = $aws_update_tag
        """

    tx.run(
        ingest_sso_policy,
        PolicyId=policy_id,
        PolicyName=policy_name,
        PolicyType=policy_type,
        PrincipalArn=principal_arn,
        consolelink=consolelink,
        PolicyArn=policy_arn,
        region="global",
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_policy(
    neo4j_session: neo4j.Session,
    policy_id: str,
    policy_name: str,
    policy_type: str,
    principal_arn: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    neo4j_session.write_transaction(
        _load_policy_tx,
        policy_id,
        policy_name,
        policy_type,
        principal_arn,
        current_aws_account_id,
        aws_update_tag,
    )


@timeit
def load_policy_statements(
    neo4j_session: neo4j.Session,
    policy_id: str,
    policy_name: str,
    statements: Any,
    aws_update_tag: int,
    consolelink: str,
) -> None:
    ingest_policy_statement = """
        MATCH (policy:AWSPolicy{id: $PolicyId})
        WITH policy
        UNWIND $Statements as statement_data
        MERGE (statement:AWSPolicyStatement{id: statement_data.id})
        SET
        statement.effect = statement_data.Effect,
        statement.action = statement_data.Action,
        statement.region = $region,
        statement.consolelink = $consolelink,
        statement.notaction = statement_data.NotAction,
        statement.resource = statement_data.Resource,
        statement.notresource = statement_data.NotResource,
        statement.condition = statement_data.Condition,
        statement.sid = statement_data.Sid,
        statement.lastupdated = $aws_update_tag
        MERGE (policy)-[r:STATEMENT]->(statement)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        """
    neo4j_session.run(
        ingest_policy_statement,
        PolicyId=policy_id,
        consolelink=consolelink,
        PolicyName=policy_name,
        Statements=statements,
        region="global",
        aws_update_tag=aws_update_tag,
    ).consume()


@timeit
def load_policy_data(
    neo4j_session: neo4j.Session,
    policy_map: Dict,
    policy_type: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    for principal_arn, policy_list in policy_map.items():
        logger.debug(f"Syncing IAM policies for principal {principal_arn}")
        for policy_name, statements in policy_list.items():
            consolelink = ""
            policy_id = transform_policy_id(current_aws_account_id, policy_type, policy_name)
            load_policy(
                neo4j_session,
                policy_id,
                policy_name,
                policy_type,
                principal_arn,
                current_aws_account_id,
                aws_update_tag,
            )
            load_policy_statements(neo4j_session, policy_id, policy_name, statements, aws_update_tag, consolelink)


@timeit
def sync_users(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM users for account '%s'.", current_aws_account_id)
    data = get_user_list_data(boto3_session)

    logger.info(f"Total Users: {len(data['Users'])}")

    data = transform_users_data(boto3_session, data["Users"])

    load_users(neo4j_session, data["Users"], current_aws_account_id, aws_update_tag)

    # INFO: This is a temporary solution to skip Loading Policies for Manual runs.
    if common_job_parameters.get("MANUAL_RUN", False) or current_aws_account_id == "934101271236":
        pass

    else:
        sync_user_inline_policies(boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag)

        sync_user_managed_policies(boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag)

    run_cleanup_job("aws_import_users_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync_user_managed_policies(
    boto3_session: boto3.session.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    managed_policy_data = get_user_managed_policy_data(boto3_session, data["Users"])
    transform_policy_data(managed_policy_data, PolicyType.managed.value, current_aws_account_id)
    load_policy_data(
        neo4j_session,
        managed_policy_data,
        PolicyType.managed.value,
        current_aws_account_id,
        aws_update_tag,
    )


@timeit
def sync_user_inline_policies(
    boto3_session: boto3.session.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    policy_data = get_user_policy_data(boto3_session, data["Users"])
    transform_policy_data(policy_data, PolicyType.inline.value, current_aws_account_id)
    load_policy_data(neo4j_session, policy_data, PolicyType.inline.value, current_aws_account_id, aws_update_tag)


@timeit
def sync_groups(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM groups for account '%s'.", current_aws_account_id)
    data = get_group_list_data(boto3_session)

    logger.info(f"Total Groups: {len(data['Groups'])}")

    load_groups(neo4j_session, data["Groups"], current_aws_account_id, aws_update_tag)

    # INFO: This is a temporary solution to skip Loading Policies for manual runs.
    if common_job_parameters.get("MANUAL_RUN", False) or current_aws_account_id == "934101271236":
        pass

    else:
        sync_groups_inline_policies(boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag)

        sync_group_managed_policies(boto3_session, data, neo4j_session, current_aws_account_id, aws_update_tag)

        # sync_group_service_access_details(boto3_session, data['Groups'], neo4j_session, aws_update_tag)

    run_cleanup_job("aws_import_groups_cleanup.json", neo4j_session, common_job_parameters)


def sync_group_managed_policies(
    boto3_session: boto3.session.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    managed_policy_data = get_group_managed_policy_data(boto3_session, data["Groups"])
    transform_policy_data(managed_policy_data, PolicyType.managed.value, current_aws_account_id)
    load_policy_data(
        neo4j_session,
        managed_policy_data,
        PolicyType.managed.value,
        current_aws_account_id,
        aws_update_tag,
    )


def sync_groups_inline_policies(
    boto3_session: boto3.session.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    policy_data = get_group_policy_data(boto3_session, data["Groups"])
    transform_policy_data(policy_data, PolicyType.inline.value, current_aws_account_id)
    load_policy_data(neo4j_session, policy_data, PolicyType.inline.value, current_aws_account_id, aws_update_tag)


@timeit
def sync_roles(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM roles for account '%s'.", current_aws_account_id)
    data = get_role_list_data(boto3_session)
    external_access_roles = get_external_access_roles(boto3_session, common_job_parameters)
    data = transform_roles(boto3_session, data["Roles"], external_access_roles, common_job_parameters)

    logger.info(f"Total Roles: {len(data['Roles'])}")

    load_roles(neo4j_session, data["Roles"], current_aws_account_id, aws_update_tag)

    # INFO: This is a temporary solution to skip Loading Policies for manual runs.
    if common_job_parameters.get("MANUAL_RUN", False) or current_aws_account_id == "934101271236":
        pass

    else:
        sync_role_inline_policies(current_aws_account_id, boto3_session, data, neo4j_session, aws_update_tag)

        sync_role_managed_policies(current_aws_account_id, boto3_session, data, neo4j_session, aws_update_tag)

        # sync_role_service_access_details(boto3_session, data['Roles'], neo4j_session, aws_update_tag)

    run_cleanup_job("aws_import_roles_cleanup.json", neo4j_session, common_job_parameters)


def sync_role_managed_policies(
    current_aws_account_id: str,
    boto3_session: boto3.session.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
) -> None:
    logger.info("Syncing IAM role managed policies for account '%s'.", current_aws_account_id)
    managed_policy_data = get_role_managed_policy_data(boto3_session, data["Roles"])
    transform_policy_data(managed_policy_data, PolicyType.managed.value, current_aws_account_id)
    load_policy_data(
        neo4j_session,
        managed_policy_data,
        PolicyType.managed.value,
        current_aws_account_id,
        aws_update_tag,
    )


def sync_role_inline_policies(
    current_aws_account_id: str,
    boto3_session: boto3.session.Session,
    data: Dict,
    neo4j_session: neo4j.Session,
    aws_update_tag: int,
) -> None:
    logger.info("Syncing IAM role inline policies for account '%s'.", current_aws_account_id)
    inline_policy_data = get_role_policy_data(boto3_session, data["Roles"])
    transform_policy_data(inline_policy_data, PolicyType.inline.value, current_aws_account_id)
    load_policy_data(neo4j_session, inline_policy_data, PolicyType.inline.value, current_aws_account_id, aws_update_tag)


@timeit
def sync_group_memberships(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM group membership for account '%s'.", current_aws_account_id)
    query = (
        "MATCH (group:AWSGroup)<-[:RESOURCE]-(:AWSAccount{id: $AWS_ACCOUNT_ID}) "
        "return group.name as name, group.arn as arn;"
    )
    groups = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id)
    groups_membership = {group["arn"]: get_group_membership_data(boto3_session, group["name"]) for group in groups}
    load_group_memberships(neo4j_session, groups_membership, aws_update_tag)
    run_cleanup_job(
        "aws_import_groups_membership_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_user_access_keys(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM user access keys for account '%s'.", current_aws_account_id)
    query = "MATCH (user:AWSUser)<-[:RESOURCE]-(:AWSAccount{id: $AWS_ACCOUNT_ID}) return user.name as name"
    result = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id)
    usernames = [r["name"] for r in result]
    for name in usernames:
        access_keys = get_account_access_key_data(boto3_session, name)
        if access_keys:
            consolelink = aws_console_link.get_console_link(
                arn=f"arn:aws:iam::{current_aws_account_id}:access_keys/{name}",
            )
            account_access_keys = {f"arn:aws:iam::{current_aws_account_id}:user/{name}": access_keys}
            load_user_access_keys(neo4j_session, account_access_keys, aws_update_tag, consolelink)
    run_cleanup_job(
        "aws_import_account_access_key_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


def set_used_state(session: neo4j.Session, project_id: str, common_job_parameters: Dict, update_tag: int) -> None:
    session.write_transaction(_set_used_state_tx, project_id, common_job_parameters, update_tag)


def _set_used_state_tx(
    tx: neo4j.Transaction,
    project_id: str,
    common_job_parameters: Dict,
    update_tag: int,
) -> None:
    ingest_role_used = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(n:AWSRole)
    WHERE (n)-[:TRUSTS_AWS_PRINCIPAL]->() AND n.lastupdated = $update_tag
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_role_used,
        WORKSPACE_ID=common_job_parameters["WORKSPACE_ID"],
        update_tag=update_tag,
        AWS_ID=project_id,
        isUsed=True,
    )

    ingest_entity_used = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(n)
    WHERE ()-[:TRUSTS_AWS_PRINCIPAL]->(n) AND n.lastupdated = $update_tag
    AND labels(n) IN [['AWSUser'], ['AWSGroup']]
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_entity_used,
        WORKSPACE_ID=common_job_parameters["WORKSPACE_ID"],
        update_tag=update_tag,
        AWS_ID=project_id,
        isUsed=True,
    )

    ingest_entity_unused = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(n)
    WHERE NOT EXISTS(n.isUsed) AND n.lastupdated = $update_tag
    AND labels(n) IN [['AWSUser'], ['AWSGroup'], ['AWSRole']]
    SET n.isUsed = $isUsed
    """

    tx.run(
        ingest_entity_unused,
        WORKSPACE_ID=common_job_parameters["WORKSPACE_ID"],
        update_tag=update_tag,
        AWS_ID=project_id,
        isUsed=False,
    )


@timeit
def sync_policies(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    logger.info("Syncing IAM policies for account '%s'.", current_aws_account_id)
    data = get_policies_list_data(boto3_session)

    logger.info(f"Total policies: {len(data)}")

    data = transform_policies_data(current_aws_account_id, data)

    load_policies_for_account(neo4j_session, data, current_aws_account_id, aws_update_tag)

    run_cleanup_job("aws_import_policy_cleanup.json", neo4j_session, common_job_parameters)


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

    logger.info("Syncing IAM for account '%s', at %s.", current_aws_account_id, tic)
    # This module only syncs IAM information that is in use.
    # As such only policies that are attached to a user, role or group are synced
    sync_users(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_groups(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_roles(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_group_memberships(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
    sync_policies(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)

    # INFO: This is a temporary solution to skip Loading Assume Role relationships, Access Keys and Analysis Jobs for manual runs.
    if common_job_parameters.get("MANUAL_RUN", False) or current_aws_account_id == "934101271236":
        pass

    else:
        sync_assumerole_relationships(neo4j_session, current_aws_account_id, update_tag, common_job_parameters)
        sync_user_access_keys(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
        set_used_state(neo4j_session, current_aws_account_id, common_job_parameters, update_tag)

    run_cleanup_job("aws_import_principals_cleanup.json", neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process IAM: {toc - tic:0.4f} seconds")
