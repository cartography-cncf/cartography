import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_secret_list(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('secretsmanager', region_name=region)
    paginator = client.get_paginator('list_secrets')
    secrets: List[Dict] = []
    for page in paginator.paginate():
        secrets.extend(page['SecretList'])
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
        secret['LastRotatedDate'] = dict_date_to_epoch(secret, 'LastRotatedDate')
        secret['LastChangedDate'] = dict_date_to_epoch(secret, 'LastChangedDate')
        secret['LastAccessedDate'] = dict_date_to_epoch(secret, 'LastAccessedDate')
        secret['DeletedDate'] = dict_date_to_epoch(secret, 'DeletedDate')
        secret['CreatedDate'] = dict_date_to_epoch(secret, 'CreatedDate')

    neo4j_session.run(
        ingest_secrets,
        Secrets=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_secrets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_secrets_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing Secrets Manager for region '%s' in account '%s'.", region, current_aws_account_id)
        secrets = get_secret_list(boto3_session, region)
        load_secrets(neo4j_session, secrets, region, current_aws_account_id, update_tag)
    cleanup_secrets(neo4j_session, common_job_parameters)
