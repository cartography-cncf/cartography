import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_ses_identity(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    identity_names = []
    try:
        client = boto3_session.client('ses', region_name=region, config=get_botocore_config())
        paginator = client.get_paginator('list_identities')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            identity_names.extend(page.get('Identities', []))

        return identity_names

    except (ClientError, ConnectTimeoutError, EndpointConnectionError) as e:
        logger.error(f'Failed to call SES list_identities: {region} - {e}')
        return identity_names


@timeit
def transform_identities(boto3_session: boto3.session.Session, ids_names: List[Dict], region: str, current_aws_account_id: str) -> List[Dict]:
    resources = []
    try:
        client = boto3_session.client('ses', region_name=region, config=get_botocore_config())

        identity_verifications: dict = {}
        dkim_attributes: dict = {}

        for i in range(0, len(ids_names), 100):
            batch = ids_names[i:i + 100]

            identity_verifications.update(
                client.get_identity_verification_attributes(
                    Identities=batch,
                ).get('VerificationAttributes', {}),
            )

            dkim_attributes.update(client.get_identity_dkim_attributes(Identities=ids_names).get('DkimAttributes', {}))

        for identity_name in ids_names:
            identity = {
                'name': identity_name,
                'arn': f"arn:aws:ses:{region}:{current_aws_account_id}:identity/{identity_name}",
                'consolelink': aws_console_link.get_console_link(arn=f"arn:aws:ses:{region}:{current_aws_account_id}:identity/{identity_name}"),
                'region': region,
                'dkim': dkim_attributes.get(identity_name, {}),
                'verification': identity_verifications.get(identity_name, {}),
            }
            resources.append(identity)

    except (ClientError, ConnectTimeoutError, EndpointConnectionError) as e:
        logger.error(f'Failed to call SES get_identity_dkim_attributes: {region} - {e}')

    return resources


def load_ses_identity(session: neo4j.Session, identities: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.execute_write(_load_ses_identity_tx, identities, current_aws_account_id, aws_update_tag)


@timeit
def _load_ses_identity_tx(tx: neo4j.Transaction, identities: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (identity:AWSSESIdentity{id: record.arn})
    ON CREATE SET identity.firstseen = timestamp(),
        identity.arn = record.arn
    SET identity.lastupdated = $aws_update_tag,
        identity.name = record.name,
        identity.region = record.region,
        identity.consolelink = record.consolelink,
        identity.dkim_enabled = record.dkim.DkimEnabled,
        identity.dkim_verification_status = record.dkim.DkimVerificationStatus,
        identity.verification_status = record.verification.VerificationStatus
    WITH identity
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(identity)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=identities,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_ses_identities(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_ses_identity_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,


) -> None:
    tic = time.perf_counter()

    logger.info("Syncing SES for account '%s', at %s.", current_aws_account_id, tic)

    ses_enabled_regions = ["af-south-1", "ap-northeast-1", "ap-northeast-2", "ap-northeast-3", "ap-south-1", "ap-southeast-1", "ap-southeast-2", "ap-southeast-3", "ca-central-1", "eu-central-1", "eu-north-1", "eu-south-1", "eu-west-1", "eu-west-2", "eu-west-3", "il-central-1", "me-south-1", "sa-east-1", "us-east-1", "us-east-2", "us-west-1", "us-west-2"]

    identities = []
    for region in regions:
        logger.info("Syncing SES for region '%s' in account '%s'.", region, current_aws_account_id)

        if region not in ses_enabled_regions:
            continue

        ids = get_ses_identity(boto3_session, region)
        identities.extend(transform_identities(boto3_session, ids, region, current_aws_account_id))

    logger.info(f"Total SES Identities: {len(identities)}")

    load_ses_identity(neo4j_session, identities, current_aws_account_id, update_tag)
    cleanup_ses_identities(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process SES Service: {toc - tic:0.4f} seconds")
