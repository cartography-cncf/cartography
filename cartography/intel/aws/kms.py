import json
import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple

import boto3
import botocore
import neo4j
from botocore.exceptions import ClientError
from policyuniverse.policy import Policy

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_kms_key_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client("kms", region_name=region)
    paginator = client.get_paginator("list_keys")
    key_list: List[Any] = []
    for page in paginator.paginate():
        key_list.extend(page["Keys"])

    described_key_list = []
    for key in key_list:
        try:
            response = client.describe_key(KeyId=key["KeyId"])["KeyMetadata"]
        except ClientError as e:
            logger.warning(
                "Failed to describe key with key id - {}. Error - {}".format(
                    key["KeyId"],
                    e,
                ),
            )
            continue

        described_key_list.append(response)

    return described_key_list


@timeit
@aws_handle_regions
def get_kms_key_details(
    boto3_session: boto3.session.Session,
    kms_key_data: Dict,
    region: str,
) -> Generator[Any, Any, Any]:
    """
    Iterates over all KMS Keys.
    """
    client = boto3_session.client("kms", region_name=region)
    for key in kms_key_data:
        policy = get_policy(key, client)
        aliases = get_aliases(key, client)
        grants = get_grants(key, client)
        yield key["KeyId"], policy, aliases, grants


@timeit
def get_policy(key: Dict, client: botocore.client.BaseClient) -> Any:
    """
    Gets the KMS Key policy. Returns policy string or None if we are unable to retrieve it.
    """
    try:
        policy = client.get_key_policy(KeyId=key["KeyId"], PolicyName="default")
    except ClientError as e:
        policy = None
        if e.response["Error"]["Code"] == "AccessDeniedException":
            logger.warning(
                f"kms:get_key_policy on key id {key['KeyId']} failed with AccessDeniedException; continuing sync.",
                exc_info=True,
            )
        else:
            raise

    return policy


@timeit
def get_aliases(key: Dict, client: botocore.client.BaseClient) -> List[Any]:
    """
    Gets the KMS Key Aliases.
    """
    aliases: List[Any] = []
    paginator = client.get_paginator("list_aliases")
    for page in paginator.paginate(KeyId=key["KeyId"]):
        aliases.extend(page["Aliases"])

    return aliases


@timeit
def get_grants(key: Dict, client: botocore.client.BaseClient) -> List[Any]:
    """
    Gets the KMS Key Grants.
    """
    grants: List[Any] = []
    paginator = client.get_paginator("list_grants")
    try:
        for page in paginator.paginate(KeyId=key["KeyId"]):
            grants.extend(page["Grants"])
    except ClientError as e:
        if e.response["Error"]["Code"] == "AccessDeniedException":
            logger.warning(
                f'kms:list_grants on key_id {key["KeyId"]} failed with AccessDeniedException; continuing sync.',
                exc_info=True,
            )
        else:
            raise
    return grants


@timeit
def _load_kms_key_aliases(
    neo4j_session: neo4j.Session,
    aliases: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest KMS Aliases into neo4j.
    """
    ingest_aliases = """
    UNWIND $alias_list AS alias
    MERGE (a:KMSAlias{id: alias.AliasArn})
    ON CREATE SET a.firstseen = timestamp(), a.targetkeyid = alias.TargetKeyId
    SET a.aliasname = alias.AliasName, a.lastupdated = $UpdateTag
    WITH a, alias
    MATCH (kmskey:KMSKey{id: alias.TargetKeyId})
    MERGE (a)-[r:KNOWN_AS]->(kmskey)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    neo4j_session.run(
        ingest_aliases,
        alias_list=aliases,
        UpdateTag=update_tag,
    )


@timeit
def _load_kms_key_grants(
    neo4j_session: neo4j.Session,
    grants_list: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest KMS Key Grants into neo4j.
    """
    ingest_grants = """
    UNWIND $grants AS grant
    MERGE (g:KMSGrant{id: grant.GrantId})
    ON CREATE SET g.firstseen = timestamp(), g.granteeprincipal = grant.GranteePrincipal,
    g.creationdate = grant.CreationDate
    SET g.name = grant.GrantName, g.lastupdated = $UpdateTag
    WITH g, grant
    MATCH (kmskey:KMSKey{id: grant.KeyId})
    MERGE (g)-[r:APPLIED_ON]->(kmskey)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UpdateTag
    """

    # neo4j does not accept datetime objects and values. This loop is used to convert
    # these values to string.
    for grant in grants_list:
        grant["CreationDate"] = str(grant["CreationDate"])

    neo4j_session.run(
        ingest_grants,
        grants=grants_list,
        UpdateTag=update_tag,
    )


@timeit
def _load_kms_key_policies(
    neo4j_session: neo4j.Session,
    policies: List[Dict],
    update_tag: int,
) -> None:
    """
    Ingest KMS Key policy results into neo4j.
    """
    # NOTE we use the coalesce function so appending works when the value is null initially
    ingest_policies = """
    UNWIND $policies AS policy
    MATCH (k:KMSKey) where k.name = policy.kms_key
    SET k.anonymous_access = (coalesce(k.anonymous_access, false) OR policy.internet_accessible),
    k.anonymous_actions = coalesce(k.anonymous_actions, []) + policy.accessible_actions,
    k.lastupdated = $UpdateTag
    """

    neo4j_session.run(
        ingest_policies,
        policies=policies,
        UpdateTag=update_tag,
    )


def _set_default_values(neo4j_session: neo4j.Session, aws_account_id: str) -> None:
    set_defaults = """
    MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(kmskey:KMSKey) where kmskey.anonymous_actions IS NULL
    SET kmskey.anonymous_access = false, kmskey.anonymous_actions = []
    """

    neo4j_session.run(
        set_defaults,
        AWS_ID=aws_account_id,
    )


@timeit
def load_kms_key_details(
    neo4j_session: neo4j.Session,
    policy_alias_grants_data: List[Tuple[Any, Any, Any, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Create dictionaries for all KMS key policies, aliases and grants so we can import them in a single query for each
    """
    policies = []
    aliases: List[str] = []
    grants: List[str] = []
    for key, policy, alias, grant in policy_alias_grants_data:
        parsed_policy = parse_policy(key, policy)
        if parsed_policy is not None:
            policies.append(parsed_policy)
        if len(alias) > 0:
            aliases.extend(alias)
        if len(grants) > 0:
            grants.extend(grant)

    # cleanup existing policy properties
    run_cleanup_job(
        "aws_kms_details.json",
        neo4j_session,
        {"UPDATE_TAG": update_tag, "AWS_ID": aws_account_id},
    )

    _load_kms_key_policies(neo4j_session, policies, update_tag)
    _load_kms_key_aliases(neo4j_session, aliases, update_tag)
    _load_kms_key_grants(neo4j_session, grants, update_tag)
    _set_default_values(neo4j_session, aws_account_id)


@timeit
def parse_policy(key: str, policy: Policy) -> Optional[Dict[Any, Any]]:
    """
    Uses PolicyUniverse to parse KMS key policies and returns the internet accessibility results
    """
    # policy is not required, so may be None
    # policy JSON format. Note condition can be any JSON statement so will need to import as-is
    # policy is a very complex format, so the policyuniverse library will be used for parsing out important data
    # ...metadata...
    # "Policy" :
    # {
    #   "Version": "2012-10-17",
    #   "Id": "key-consolepolicy-5",
    #   "Statement": [
    #     {
    #       "Sid": "Enable IAM User Permissions",
    #       "Effect": "Allow",
    #       "Principal": {
    #         "AWS": "arn:aws:iam::123456789012:root"
    #       },
    #       "Action": "kms:*",
    #       "Resource": "*"
    #     },
    #     {
    #       "Sid": "Allow access for Key Administrators",
    #       "Effect": "Allow",
    #       "Principal": {
    #         "AWS": "arn:aws:iam::123456789012:role/ec2-manager"
    #       },
    #       "Action": [
    #         "kms:Create*",
    #         "kms:Describe*",
    #         "kms:Enable*",
    #         "kms:List*",
    #         "kms:Put*",
    #         "kms:Update*",
    #         "kms:Revoke*",
    #         "kms:Disable*",
    #         "kms:Get*",
    #         "kms:Delete*",
    #         "kms:ScheduleKeyDeletion",
    #         "kms:CancelKeyDeletion"
    #       ],
    #       "Resource": "*"
    #     }
    #   ]
    # }
    if policy is not None:
        # get just the policy element and convert to JSON because boto3 returns this as string
        policy = Policy(json.loads(policy["Policy"]))
        if policy.is_internet_accessible():
            return {
                "kms_key": key,
                "internet_accessible": True,
                "accessible_actions": list(policy.internet_accessible_actions()),
            }
        else:
            return None
    else:
        return None


@timeit
def load_kms_keys(
    neo4j_session: neo4j.Session,
    data: Dict,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_keys = """
    UNWIND $key_list AS k
    MERGE (kmskey:KMSKey{id:k.KeyId})
    ON CREATE SET kmskey.firstseen = timestamp(),
    kmskey.arn = k.Arn, kmskey.creationdate = k.CreationDate
    SET kmskey.deletiondate = k.DeletionDate,
    kmskey.validto = k.ValidTo,
    kmskey.enabled = k.Enabled,
    kmskey.keystate = k.KeyState,
    kmskey.customkeystoreid = k.CustomKeyStoreId,
    kmskey.cloudhsmclusterid = k.CloudHsmClusterId,
    kmskey.lastupdated = $aws_update_tag,
    kmskey.region = $Region
    WITH kmskey
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(kmskey)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    # neo4j does not accept datetime objects and values. This loop is used to convert
    # these values to string.
    for key in data:
        key["CreationDate"] = str(key["CreationDate"])
        key["DeletionDate"] = str(key.get("DeletionDate"))
        key["ValidTo"] = str(key.get("ValidTo"))

    neo4j_session.run(
        ingest_keys,
        key_list=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_kms(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job("aws_import_kms_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync_kms_keys(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    kms_keys = get_kms_key_list(boto3_session, region)

    load_kms_keys(
        neo4j_session,
        kms_keys,
        region,
        current_aws_account_id,
        aws_update_tag,
    )

    policy_alias_grants_data = get_kms_key_details(boto3_session, kms_keys, region)
    load_kms_key_details(
        neo4j_session,
        policy_alias_grants_data,
        region,
        current_aws_account_id,
        aws_update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing KMS for region %s in account '%s'.",
            region,
            current_aws_account_id,
        )
        sync_kms_keys(
            neo4j_session,
            boto3_session,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup_kms(neo4j_session, common_job_parameters)
