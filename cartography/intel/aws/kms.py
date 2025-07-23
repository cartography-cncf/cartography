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

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.kms.aliases import KMSAliasSchema
from cartography.models.aws.kms.grants import KMSGrantSchema
from cartography.models.aws.kms.keys import KMSKeySchema
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
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
def transform_kms_aliases(aliases: List[Dict]) -> List[Dict]:
    """
    Transform AWS KMS Aliases to match the data model.
    Converts datetime fields to epoch timestamps for consistency.
    """
    transformed_data = []
    for alias in aliases:
        transformed = dict(alias)
        
        # Convert datetime fields to epoch timestamps
        transformed["CreationDate"] = dict_date_to_epoch(alias, "CreationDate")
        transformed["LastUpdatedDate"] = dict_date_to_epoch(alias, "LastUpdatedDate")
        
        transformed_data.append(transformed)
    return transformed_data


@timeit
def transform_kms_keys(keys: List[Dict]) -> List[Dict]:
    """
    Transform AWS KMS Keys to match the data model.
    Converts datetime fields to epoch timestamps for consistency.
    """
    transformed_data = []
    for key in keys:
        transformed = dict(key)
        
        # Convert datetime fields to epoch timestamps
        transformed["CreationDate"] = dict_date_to_epoch(key, "CreationDate")
        transformed["DeletionDate"] = dict_date_to_epoch(key, "DeletionDate") 
        transformed["ValidTo"] = dict_date_to_epoch(key, "ValidTo")
        
        transformed_data.append(transformed)
    return transformed_data


@timeit
def transform_kms_grants(grants: List[Dict]) -> List[Dict]:
    """
    Transform AWS KMS Grants to match the data model.
    Converts datetime fields to epoch timestamps for consistency.
    """
    transformed_data = []
    for grant in grants:
        transformed = dict(grant)
        
        # Convert datetime fields to epoch timestamps
        transformed["CreationDate"] = dict_date_to_epoch(grant, "CreationDate")
        
        transformed_data.append(transformed)
    return transformed_data


@timeit
def load_kms_aliases(
    neo4j_session: neo4j.Session,
    aliases: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load KMS Aliases into Neo4j using the data model.
    """
    logger.info(f"Loading {len(aliases)} KMS aliases for region {region} into graph.")
    load(
        neo4j_session,
        KMSAliasSchema(),
        aliases,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def load_kms_grants(
    neo4j_session: neo4j.Session,
    grants: List[Dict],
    update_tag: int,
) -> None:
    """
    Load KMS Grants into Neo4j using the data model.
    """
    logger.info(f"Loading {len(grants)} KMS grants into graph.")
    load(
        neo4j_session,
        KMSGrantSchema(),
        grants,
        lastupdated=update_tag,
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
    aliases: List[Dict] = []
    grants: List[Dict] = []
    for key, policy, alias, grant in policy_alias_grants_data:
        parsed_policy = parse_policy(key, policy)
        if parsed_policy is not None:
            policies.append(parsed_policy)
        if len(alias) > 0:
            aliases.extend(alias)
        if len(grant) > 0:
            grants.extend(grant)

    # cleanup existing policy properties
    run_cleanup_job(
        "aws_kms_details.json",
        neo4j_session,
        {"UPDATE_TAG": update_tag, "AWS_ID": aws_account_id},
    )

    _load_kms_key_policies(neo4j_session, policies, update_tag)
    
    # Transform and load aliases using the data model
    transformed_aliases = transform_kms_aliases(aliases)
    load_kms_aliases(neo4j_session, transformed_aliases, region, aws_account_id, update_tag)
    
    # Transform and load grants using the data model
    transformed_grants = transform_kms_grants(grants)
    load_kms_grants(neo4j_session, transformed_grants, update_tag)
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
    keys: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load KMS Keys into Neo4j using the data model.
    Expects data to already be transformed by transform_kms_keys().
    """
    logger.info(f"Loading {len(keys)} KMS keys for region {region} into graph.")
    load(
        neo4j_session,
        KMSKeySchema(),
        keys,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def cleanup_kms(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Run KMS cleanup using schema-based GraphJobs for all node types.
    """
    logger.debug("Running KMS cleanup using GraphJob for all node types")
    
    # Clean up grants first (they depend on keys)
    GraphJob.from_node_schema(KMSGrantSchema(), common_job_parameters).run(neo4j_session)
    
    # Clean up aliases
    GraphJob.from_node_schema(KMSAliasSchema(), common_job_parameters).run(neo4j_session)
    
    # Clean up keys
    GraphJob.from_node_schema(KMSKeySchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_kms_keys(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    kms_keys = get_kms_key_list(boto3_session, region)

    # Transform and load keys using the data model
    transformed_keys = transform_kms_keys(kms_keys)
    load_kms_keys(
        neo4j_session,
        transformed_keys,
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
