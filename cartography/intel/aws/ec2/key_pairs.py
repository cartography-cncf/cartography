import logging

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_key_pairs(boto3_session, region):
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    return client.describe_key_pairs()['KeyPairs']


@timeit
def load_ec2_key_pairs(neo4j_session, data, region, current_aws_account_id, aws_update_tag):
    ingest_key_pair = """
    MERGE (keypair:KeyPair:EC2KeyPair{arn: {ARN}, id: {ARN}})
    ON CREATE SET keypair.firstseen = timestamp()
    SET keypair.keyname = {KeyName}, keypair.keyfingerprint = {KeyFingerprint}, keypair.region = {Region},
    keypair.lastupdated = {aws_update_tag}
    WITH keypair
    MATCH (aa:AWSAccount{id: {AWS_ACCOUNT_ID}})
    MERGE (aa)-[r:RESOURCE]->(keypair)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = {aws_update_tag}
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
            aws_update_tag=aws_update_tag,
        )


@timeit
def cleanup_ec2_key_pairs(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_ec2_key_pairs_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_ec2_key_pairs(
    neo4j_session, boto3_session, regions, current_aws_account_id, aws_update_tag,
    common_job_parameters,
):
    for region in regions:
        logger.debug("Syncing EC2 key pairs for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_ec2_key_pairs(boto3_session, region)
        load_ec2_key_pairs(neo4j_session, data, region, current_aws_account_id, aws_update_tag)
    cleanup_ec2_key_pairs(neo4j_session, common_job_parameters)
