import logging
from typing import Dict
from typing import List

import boto3
import neo4j
from dateutil import parser

from cartography.client.core.tx import run_write_query
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_hub(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client("securityhub")
    try:
        return client.describe_hub()
    except client.exceptions.ResourceNotFoundException:
        return {}
    except client.exceptions.InvalidAccessException:
        return {}


def transform_hub(hub_data: Dict) -> None:
    if "SubscribedAt" in hub_data and hub_data["SubscribedAt"]:
        subbed_at = parser.parse(hub_data["SubscribedAt"])
        hub_data["SubscribedAt"] = int(subbed_at.timestamp())
    else:
        hub_data["SubscribedAt"] = None


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
    SET n.subscribed_at = hub.SubscribedAt, n.auto_enable_controls = hub.AutoEnableControls,
        n.lastupdated = $aws_update_tag
    WITH n
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(n)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    run_write_query(
        neo4j_session,
        ingest_hub,
        Hub=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_securityhub(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    run_cleanup_job(
        "aws_import_securityhub_cleanup.json",
        neo4j_session,
        common_job_parameters,
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
    logger.info("Syncing Security Hub in account '%s'.", current_aws_account_id)
    hub = get_hub(boto3_session)
    if hub:
        transform_hub(hub)
        load_hub(neo4j_session, hub, current_aws_account_id, update_tag)
        cleanup_securityhub(neo4j_session, common_job_parameters)
