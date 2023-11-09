import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from .util import get_botocore_config
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.keypairs import EC2KeyPairSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_key_pairs(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    return client.describe_key_pairs()['KeyPairs']


@timeit
def load_ec2_key_pairs(
    neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_key_pair = """
    MERGE (keypair:KeyPair:EC2KeyPair{arn: $ARN, id: $ARN})
    ON CREATE SET keypair.firstseen = timestamp()
    SET keypair.keyname = $KeyName, keypair.keyfingerprint = $KeyFingerprint, keypair.region = $Region,
    keypair.lastupdated = $update_tag
    WITH keypair
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(keypair)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    for key_pair in data:
        key_name = key_pair["KeyName"]
        key_fingerprint = key_pair.get("KeyFingerprint")
        key_pair_arn = f'arn:aws:ec2:{region}:{current_aws_account_id}:key-pair/{key_name}'

        neo4j_session.run(
            ingest_key_pair,
            ARN=key_pair_arn,
            KeyName=key_name,
            KeyFingerprint=key_fingerprint,
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            update_tag=update_tag,
        )


@timeit
def cleanup_ec2_key_pairs(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(EC2KeyPairSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_ec2_key_pairs(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing EC2 key pairs for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_key_pairs(boto3_session, region)
        load_ec2_key_pairs(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_ec2_key_pairs(neo4j_session, common_job_parameters)
