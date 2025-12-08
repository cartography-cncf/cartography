import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import run_write_query
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_internet_gateways(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    return client.describe_internet_gateways()["InternetGateways"]


@timeit
def load_internet_gateways(
    neo4j_session: neo4j.Session,
    internet_gateways: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Internet Gateways in %s.", len(internet_gateways), region)
    # TODO: Right now this won't work in non-AWS commercial (GovCloud, China) as partition is hardcoded
    query = """
    UNWIND $internet_gateways as igw
        MERGE (ig:AWSInternetGateway{id: igw.InternetGatewayId})
        ON CREATE SET
            ig.firstseen = timestamp(),
            ig.region = $region
        SET
            ig.ownerid = igw.OwnerId,
            ig.lastupdated = $aws_update_tag,
            ig.arn = "arn:aws:ec2:"+$region+":"+igw.OwnerId+":internet-gateway/"+igw.InternetGatewayId
        WITH igw, ig

        MATCH (awsAccount:AWSAccount {id: $aws_account_id})
        MERGE (awsAccount)-[r:RESOURCE]->(ig)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        WITH igw, ig

        UNWIND igw.Attachments as attachment
        MATCH (vpc:AWSVpc{id: attachment.VpcId})
        MERGE (ig)-[r:ATTACHED_TO]->(vpc)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """

    run_write_query(
        neo4j_session,
        query,
        internet_gateways=internet_gateways,
        region=region,
        aws_account_id=current_aws_account_id,
        aws_update_tag=update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running Internet Gateway cleanup job.")
    run_cleanup_job(
        "aws_import_internet_gateways_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_internet_gateways(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing Internet Gateways for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        internet_gateways = get_internet_gateways(boto3_session, region)
        load_internet_gateways(
            neo4j_session,
            internet_gateways,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
