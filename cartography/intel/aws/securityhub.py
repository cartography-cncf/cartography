import datetime
import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from cloudconsolelink.clouds.aws import AWSLinker
from dateutil import parser

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
def get_hub(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client('securityhub')
    try:
        return client.describe_hub()
    except client.exceptions.ResourceNotFoundException:
        return {}
    except client.exceptions.InvalidAccessException:
        return {}


def transform_hub(hub_data: Dict) -> None:
    if 'SubscribedAt' in hub_data and hub_data['SubscribedAt']:
        subbed_at = parser.parse(hub_data['SubscribedAt'])
        hub_data['SubscribedAt'] = int(subbed_at.timestamp())

    else:
        hub_data['SubscribedAt'] = None


@timeit
def load_hub(
    neo4j_session: neo4j.Session,
    data: Dict,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_hub = """
    WITH $Hub AS hub
    MERGE (n:SecurityHub{id: hub.HubArn})
    ON CREATE SET n.firstseen = timestamp()
    SET n.subscribed_at = hub.SubscribedAt,
    n.region = $region,
    n.auto_enable_controls = hub.AutoEnableControls,
    n.lastupdated = $aws_update_tag,
    n.arn = hub.HubArn,
    n.consolelink = $consolelink
    WITH n
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        ingest_hub,
        Hub=data,
        region="global",
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
        consolelink=aws_console_link.get_console_link(arn=data.get('HubArn', '')),
    )


@timeit
def cleanup_securityhub(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_securityhub_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:

    tic = time.perf_counter()

    logger.info("Syncing Security Hub for account '%s', at %s.", current_aws_account_id, tic)

    # hub = {}
    # try:
    #     hub = get_hub(boto3_session)

    # except (ClientError, ConnectTimeoutError) as e:
    #     logger.error(f'Failed to get Security Hub details - {e}')

    # if hub:
    #     transform_hub(hub)
    #     load_hub(neo4j_session, hub, current_aws_account_id, update_tag)
    #     cleanup_securityhub(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Security Hub: {toc - tic:0.4f} seconds")
