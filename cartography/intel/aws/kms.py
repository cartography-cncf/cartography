import json
import logging
from typing import Any
from typing import Dict
from typing import Generator
from typing import List

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
    kms_key_data: List[Dict],
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
        if e.response["Error"]["Code"] == "AccessDeniedException":
            policy = None
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


def transform_kms_keys(keys: List[Dict], policy_data: Dict[str, Dict]) -> List[Dict]:
    """
    Transform AWS KMS Keys to match the data model.
    Converts datetime fields to epoch timestamps for consistency.
    Includes policy analysis properties.
    """
    transformed_data = []
    for key in keys:
        transformed = dict(key)

        # Convert datetime fields to epoch timestamps
        transformed["CreationDate"] = dict_date_to_epoch(key, "CreationDate")
        transformed["DeletionDate"] = dict_date_to_epoch(key, "DeletionDate")
        transformed["ValidTo"] = dict_date_to_epoch(key, "ValidTo")

        # Add policy analysis
        transformed.update(policy_data[key["KeyId"]])

        transformed_data.append(transformed)
    return transformed_data


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


def transform_kms_key_policies(
    policy_alias_grants_data: list[tuple],
) -> dict[str, dict[str, Any]]:
    """
    Transform KMS key policy data for inclusion in key records.
    """
    policy_data = {}

    for key_id, policy, *_ in policy_alias_grants_data:
        # Handle keys with null policy (access denied)
        if policy is None:
            logger.info(
                f"Skipping KMS key {key_id} policy due to AccessDenied; policy analysis properties will be null"
            )
            policy_data[key_id] = {
                "kms_key": key_id,
                "anonymous_access": None,
                "anonymous_actions": None,
            }
            continue

        parsed_policy = parse_policy(key_id, policy)
        policy_data[key_id] = parsed_policy

    return policy_data


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
    aws_account_id: str,
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
        AWS_ID=aws_account_id,
    )


@timeit
def parse_policy(key: str, policy: Policy) -> dict[str, Any]:
    """
    Uses PolicyUniverse to parse KMS key policies and returns the internet accessibility results.
    Expects policy to never be None
    """
    policy = Policy(json.loads(policy["Policy"]))
    inet_actions = policy.internet_accessible_actions()

    return {
        "kms_key": key,
        "anonymous_access": policy.is_internet_accessible(),
        "anonymous_actions": list(inet_actions) if inet_actions else [],
    }


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
    GraphJob.from_node_schema(KMSGrantSchema(), common_job_parameters).run(
        neo4j_session
    )

    # Clean up aliases
    GraphJob.from_node_schema(KMSAliasSchema(), common_job_parameters).run(
        neo4j_session
    )

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
    # Get basic key metadata
    kms_keys = get_kms_key_list(boto3_session, region)

    # Get detailed data (policies, aliases, grants)
    policy_alias_grants_data = list(
        get_kms_key_details(boto3_session, kms_keys, region)
    )

    # Transform policy data for inclusion in keys
    policy_data = transform_kms_key_policies(policy_alias_grants_data)

    # Transform keys WITH policy data included
    transformed_keys = transform_kms_keys(kms_keys, policy_data)

    # Load complete keys (now includes policy properties via data model)
    load_kms_keys(
        neo4j_session,
        transformed_keys,
        region,
        current_aws_account_id,
        aws_update_tag,
    )

    # Extract and transform aliases and grants
    aliases: List[Dict] = []
    grants: List[Dict] = []

    for key, policy, alias, grant in policy_alias_grants_data:
        if len(alias) > 0:
            aliases.extend(alias)
        if len(grant) > 0:
            grants.extend(grant)

    # Transform aliases and grants following standard pattern
    transformed_aliases = transform_kms_aliases(aliases)
    transformed_grants = transform_kms_grants(grants)

    # Load aliases and grants directly - standard Cartography pattern
    load_kms_aliases(
        neo4j_session,
        transformed_aliases,
        region,
        current_aws_account_id,
        aws_update_tag,
    )
    load_kms_grants(
        neo4j_session, transformed_grants, current_aws_account_id, aws_update_tag
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
