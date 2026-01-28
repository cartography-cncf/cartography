import logging
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.elastic_ip_addresses import ElasticIPAddressSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_elastic_ip_addresses(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    try:
        addresses = client.describe_addresses()["Addresses"]
    except ClientError as e:
        logger.warning(f"Failed retrieve address for region - {region}. Error - {e}")
        raise
    return addresses


@timeit
def load_elastic_ip_addresses(
    neo4j_session: neo4j.Session,
    elastic_ip_addresses: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Creates (:ElasticIpAddress)
    (:ElasticIpAddress)-[:RESOURCE]->(:AWSAccount),
    (:EC2Instance)-[:ELASTIC_IP_ADDRESS]->(:ElasticIpAddress),
    (:NetworkInterface)-[:ELASTIC_IP_ADDRESS]->(:ElasticIpAddress),
    """
    logger.info(
        f"Loading {len(elastic_ip_addresses)} Elastic IP Addresses in {region}.",
    )
    load(
        neo4j_session,
        ElasticIPAddressSchema(),
        elastic_ip_addresses,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_elastic_ip_addresses(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(
        ElasticIPAddressSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_elastic_ip_addresses(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            f"Syncing Elastic IP Addresses for region {region} in account {current_aws_account_id}.",
        )
        addresses = get_elastic_ip_addresses(boto3_session, region)
        load_elastic_ip_addresses(
            neo4j_session,
            addresses,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_elastic_ip_addresses(neo4j_session, common_job_parameters)
