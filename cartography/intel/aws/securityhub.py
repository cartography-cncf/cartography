import logging
from typing import Any

import boto3
import neo4j
from dateutil import parser

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.securityhub import SecurityHubSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_hub(boto3_session: boto3.session.Session) -> dict:
    client = create_boto3_client(boto3_session, "securityhub")
    try:
        return client.describe_hub()
    except client.exceptions.ResourceNotFoundException:
        return {}
    except client.exceptions.InvalidAccessException:
        return {}


def transform_hub(hub_data: dict) -> None:
    if "SubscribedAt" in hub_data and hub_data["SubscribedAt"]:
        subbed_at = parser.parse(hub_data["SubscribedAt"])
        hub_data["SubscribedAt"] = int(subbed_at.timestamp())
    else:
        hub_data["SubscribedAt"] = None


@timeit
def load_hub(
    neo4j_session: neo4j.Session,
    data: dict[str, Any],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        SecurityHubSchema(),
        [data],
        lastupdated=aws_update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_securityhub(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    GraphJob.from_node_schema(SecurityHubSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing Security Hub in account '%s'.", current_aws_account_id)
    hub = get_hub(boto3_session)
    if hub:
        transform_hub(hub)
        load_hub(neo4j_session, hub, current_aws_account_id, update_tag)
        cleanup_securityhub(neo4j_session, common_job_parameters)
