import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.secretsmanager.secret_version import (
    SecretsManagerSecretVersionSchema,
)
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
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


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_secrets = """
    UNWIND $Secrets as secret
        MERGE (s:SecretsManagerSecret{id: secret.ARN})
        ON CREATE SET s.firstseen = timestamp()
        SET s.name = secret.Name, s.arn = secret.ARN, s.description = secret.Description,
            s.kms_key_id = secret.KmsKeyId, s.rotation_enabled = secret.RotationEnabled,
            s.rotation_lambda_arn = secret.RotationLambdaARN,
            s.rotation_rules_automatically_after_days = secret.RotationRules.AutomaticallyAfterDays,
            s.last_rotated_date = secret.LastRotatedDate, s.last_changed_date = secret.LastChangedDate,
            s.last_accessed_date = secret.LastAccessedDate, s.deleted_date = secret.DeletedDate,
            s.owning_service = secret.OwningService, s.created_date = secret.CreatedDate,
            s.primary_region = secret.PrimaryRegion, s.region = $Region,
            s.lastupdated = $aws_update_tag
        WITH s
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(s)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    for secret in data:
        secret["LastRotatedDate"] = dict_date_to_epoch(secret, "LastRotatedDate")
        secret["LastChangedDate"] = dict_date_to_epoch(secret, "LastChangedDate")
        secret["LastAccessedDate"] = dict_date_to_epoch(secret, "LastAccessedDate")
        secret["DeletedDate"] = dict_date_to_epoch(secret, "DeletedDate")
        secret["CreatedDate"] = dict_date_to_epoch(secret, "CreatedDate")

    neo4j_session.run(
        ingest_secrets,
        Secrets=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_secrets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "aws_import_secrets_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


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
    region: str,
    aws_account_id: str,
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

        load_secrets(neo4j_session, secrets, region, current_aws_account_id, update_tag)

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

        transformed_data = transform_secret_versions(
            all_versions,
            region,
            current_aws_account_id,
        )

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
