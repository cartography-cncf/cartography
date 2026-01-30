import logging
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.reserved_instances import EC2ReservedInstanceSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_reserved_instances(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    try:
        reserved_instances = client.describe_reserved_instances()["ReservedInstances"]
    except ClientError as e:
        logger.warning(
            f"Failed retrieve reserved instances for region - {region}. Error - {e}",
        )
        raise
    return reserved_instances


def transform_reserved_instances(data: List[Dict]) -> List[Dict]:
    """
    Transform reserved instances data, converting datetime fields to strings.
    """
    for r_instance in data:
        r_instance["Start"] = str(r_instance["Start"])
        r_instance["End"] = str(r_instance["End"])
    return data


@timeit
def load_reserved_instances(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2ReservedInstanceSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_reserved_instances(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(
        EC2ReservedInstanceSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_ec2_reserved_instances(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.debug(
            "Syncing reserved instances for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_reserved_instances(boto3_session, region)
        transform_reserved_instances(data)
        load_reserved_instances(
            neo4j_session,
            data,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_reserved_instances(neo4j_session, common_job_parameters)
