import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.secretsmanager.secret import SecretsManagerSecretSchema
from cartography.models.aws.secretsmanager.secret_version import (
    SecretsManagerSecretVersionSchema,
)
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_secret_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client("secretsmanager", region_name=region)
    paginator = client.get_paginator("list_secrets")
    secrets: List[Dict] = []
    for page in paginator.paginate():
        secrets.extend(page["SecretList"])
    return secrets


def transform_secrets(
    secrets: List[Dict],
) -> List[Dict]:
    """
    Transform AWS Secrets Manager Secrets to match the data model.
    """
    transformed_data = []
    for secret in secrets:
        # Start with a copy of the original secret data
        transformed = dict(secret)

        # Convert date fields to epoch timestamps
        transformed["CreatedDate"] = dict_date_to_epoch(secret, "CreatedDate")
        transformed["LastRotatedDate"] = dict_date_to_epoch(secret, "LastRotatedDate")
        transformed["LastChangedDate"] = dict_date_to_epoch(secret, "LastChangedDate")
        transformed["LastAccessedDate"] = dict_date_to_epoch(secret, "LastAccessedDate")
        transformed["DeletedDate"] = dict_date_to_epoch(secret, "DeletedDate")

        # Flatten nested RotationRules.AutomaticallyAfterDays property
        if "RotationRules" in secret and secret["RotationRules"]:
            rotation_rules = secret["RotationRules"]
            if "AutomaticallyAfterDays" in rotation_rules:
                transformed["RotationRulesAutomaticallyAfterDays"] = rotation_rules[
                    "AutomaticallyAfterDays"
                ]

        transformed_data.append(transformed)

    return transformed_data


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load transformed secrets into Neo4j using the data model.
    Expects data to already be transformed by transform_secrets().
    """
    logger.info(f"Loading {len(data)} Secrets for region {region} into graph.")

    # Load using the schema-based approach
    load(
        neo4j_session,
        SecretsManagerSecretSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_secrets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Run Secrets cleanup job using the data model.
    """
    logger.debug("Running Secrets cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        SecretsManagerSecretSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


@timeit
@aws_handle_regions
def get_secret_versions(
    boto3_session: boto3.session.Session, region: str, secret_arn: str
) -> List[Dict]:
    """
    Get all versions of a secret from AWS Secrets Manager.

    Note: list_secret_version_ids is not paginatable through boto3's paginator,
    so we implement manual pagination.
    """
    client = boto3_session.client("secretsmanager", region_name=region)
    next_token = None
    versions = []

    while True:
        params = {"SecretId": secret_arn, "IncludeDeprecated": True}
        if next_token:
            params["NextToken"] = next_token

        response = client.list_secret_version_ids(**params)

        for version in response.get("Versions", []):
            version["SecretId"] = secret_arn
            version["ARN"] = f"{secret_arn}:version:{version['VersionId']}"

        versions.extend(response.get("Versions", []))

        next_token = response.get("NextToken")
        if not next_token:
            break

    return versions


def transform_secret_versions(
    versions: List[Dict],
) -> List[Dict]:
    """
    Transform AWS Secrets Manager Secret Versions to match the data model.
    """
    transformed_data = []
    for version in versions:
        transformed = {
            "ARN": version["ARN"],
            "SecretId": version["SecretId"],
            "VersionId": version["VersionId"],
            "VersionStages": version.get("VersionStages"),
            "CreatedDate": dict_date_to_epoch(version, "CreatedDate"),
        }

        if "KmsKeyId" in version and version["KmsKeyId"]:
            transformed["KmsKeyId"] = version["KmsKeyId"]

        if "Tags" in version and version["Tags"]:
            transformed["Tags"] = version["Tags"]

        transformed_data.append(transformed)

    return transformed_data


@timeit
def load_secret_versions(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load secret versions into Neo4j using the data model.
    """
    logger.info(f"Loading {len(data)} Secret Versions for region {region} into graph.")

    load(
        neo4j_session,
        SecretsManagerSecretVersionSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def cleanup_secret_versions(
    neo4j_session: neo4j.Session, common_job_parameters: Dict
) -> None:
    """
    Run Secret Versions cleanup job.
    """
    logger.debug("Running Secret Versions cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        SecretsManagerSecretVersionSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync AWS Secrets Manager resources.
    """
    for region in regions:
        logger.info(
            f"Syncing Secrets Manager for region '{region}' in account '{current_aws_account_id}'."
        )
        secrets = get_secret_list(boto3_session, region)

        transformed_secrets = transform_secrets(secrets)

        load_secrets(
            neo4j_session,
            transformed_secrets,
            region,
            current_aws_account_id,
            update_tag,
        )

        all_versions = []
        for secret in secrets:
            logger.info(
                f"Getting versions for secret {secret.get('Name', 'unnamed')} ({secret['ARN']})"
            )
            versions = get_secret_versions(boto3_session, region, secret["ARN"])
            logger.info(
                f"Found {len(versions)} versions for secret {secret.get('Name', 'unnamed')}"
            )
            all_versions.extend(versions)

        transformed_data = transform_secret_versions(all_versions)

        load_secret_versions(
            neo4j_session,
            transformed_data,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup_secrets(neo4j_session, common_job_parameters)
    cleanup_secret_versions(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="SecretsManagerSecretVersion",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
