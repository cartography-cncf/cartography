import logging
from typing import Any
from typing import Dict

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.ec2.keypair import EC2KeyPairSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_key_pairs(boto3_session: boto3.session.Session, region: str) -> list[dict[str, Any]]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    return client.describe_key_pairs()['KeyPairs']


def transform_ec2_key_pairs(
        key_pairs: list[dict[str, Any]],
        region: str,
        current_aws_account_id: str,
) -> list[dict[str, Any]]:
    transformed_key_pairs = []
    for key_pair in key_pairs:
        key_name = key_pair["KeyName"]
        transformed_key_pairs.append({
            'KeyPairArn': f'arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}',
            'KeyName': key_name,
            'KeyFingerprint': key_pair.get("KeyFingerprint"),
        })
    return transformed_key_pairs


@timeit
def load_ec2_key_pairs(
        neo4j_session: neo4j.Session,
        data: list[dict[str, Any]],
        region: str,
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    # Load EC2 keypairs as known by describe-key-pairs
    logger.info(f"Loading {len(data)} EC2 keypairs for region '{region}' into graph.")
    load(
        neo4j_session,
        EC2KeyPairSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_ec2_key_pairs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(EC2KeyPairSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_ec2_key_pairs(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info("Syncing EC2 key pairs for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_key_pairs(boto3_session, region)
        transformed_data = transform_ec2_key_pairs(data, region, current_aws_account_id)
        load_ec2_key_pairs(neo4j_session, transformed_data, region, current_aws_account_id, update_tag)
    cleanup_ec2_key_pairs(neo4j_session, common_job_parameters)
