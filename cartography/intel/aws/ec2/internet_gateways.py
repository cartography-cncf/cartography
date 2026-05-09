import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j
from cloudconsolelink.clouds.aws import AWSLinker

from .util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit
# from cartography.intel.aws.util.common import get_default_vpc

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


def get_default_vpc(ec2_client):
    try:
        response = ec2_client.describe_vpcs(
            Filters=[{'Name': 'isDefault', 'Values': ['true']}],
        )
        vpcs = response.get('Vpcs', [])

        if not vpcs:
            logger.info("No default VPC found.")
            return {}

        return vpcs[0]

    except Exception as e:
        logger.error(f"Error fetching default VPC: {e}")
        return {}


@timeit
@aws_handle_regions
def get_internet_gateways(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    internet_gateways = []
    try:
        client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
        internet_gateways = client.describe_internet_gateways()['InternetGateways']

        default_vpc = get_default_vpc(client)

        if default_vpc:
            default_vpc_id = default_vpc.get('VpcId')

            # fetching the creation time of the default VPC
            vpc_response = client.describe_vpcs(VpcIds=[default_vpc_id])
            vpc_creation_time = vpc_response['Vpcs'][0].get('CreateTime') if vpc_response['Vpcs'] else None

            for igw in internet_gateways:
                # marking the igw as user by default
                igw['isDefault'] = False

                vpc_attachments = igw.get('Attachments', [])
                if vpc_attachments:
                    # checking if IGW is attached to default VPC as the previous logic
                    is_attached_to_default_vpc = any(
                        attachment.get('VpcId') == default_vpc_id
                        for attachment in vpc_attachments
                    )

                    if is_attached_to_default_vpc:
                        # fetching the creation time of the igw if it is attached to the default VPC
                        igw_response = client.describe_internet_gateways(
                            InternetGatewayIds=[igw['InternetGatewayId']],
                        )
                        igw_creation_time = igw_response['InternetGateways'][0].get('CreateTime') if igw_response['InternetGateways'] else None

                        # if IGW was created within 1 minute of default VPC creation, it would be set to as predefined
                        if vpc_creation_time and igw_creation_time:
                            time_difference = abs((igw_creation_time - vpc_creation_time).total_seconds())
                            if time_difference <= 60:
                                igw['isDefault'] = True
        else:
            # if no default VPC exists, all IGWs are user-created
            for igw in internet_gateways:
                igw['isDefault'] = False

    except Exception as e:
        logger.warning(f"Failed to retrieve internet gateways for region - {region}. Error - {e}")

    return internet_gateways


@timeit
def load_internet_gateways(
    neo4j_session: neo4j.Session, internet_gateways: List[Dict], region: str,
    current_aws_account_id: str, update_tag: int,
) -> None:
    logger.info("Loading %d Internet Gateways in %s.", len(internet_gateways), region)
    # TODO: Right now this won't work in non-AWS commercial (GovCloud, China) as partition is hardcoded
    for igw in internet_gateways:
        arn = f"arn:aws:ec2:{region}:{igw.get('OwnerId', '')}:internet-gateway/{igw['InternetGatewayId']}"
        igw['consolelink'] = aws_console_link.get_console_link(arn=arn)
    query = """
    UNWIND $internet_gateways as igw
        MERGE (ig:AWSInternetGateway{id: igw.InternetGatewayId})
        ON CREATE SET
            ig.firstseen = timestamp(),
            ig.region = $region
        SET
            ig.ownerid = igw.OwnerId,
            ig.lastupdated = $aws_update_tag,
            ig.arn = "arn:aws:ec2:"+$region+":"+igw.OwnerId+":internet-gateway/"+igw.InternetGatewayId,
            ig.is_default = igw.isDefault,
            ig.consolelink = igw.consolelink
        WITH igw, ig

        MATCH (awsAccount:AWSAccount {id: $aws_account_id})
        MERGE (awsAccount)-[r:RESOURCE]->(ig)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        WITH igw, ig

        UNWIND igw.Attachments as attachment
        MATCH (vpc:AWSVpc{id: attachment.VpcId})
        MERGE (vpc)-[r:ATTACHED_TO]->(ig)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        query,
        internet_gateways=internet_gateways,
        region=region,
        aws_account_id=current_aws_account_id,
        aws_update_tag=update_tag,
    ).consume()


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running Internet Gateway cleanup job.")
    run_cleanup_job('aws_import_internet_gateways_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_internet_gateways(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()
    logger.info("Syncing EC2 Internet Gateways for account '%s', at %s.", current_aws_account_id, tic)

    for region in regions:
        logger.info("Syncing Internet Gateways for region '%s' in account '%s'.", region, current_aws_account_id)
        internet_gateways = get_internet_gateways(boto3_session, region)

        logger.info(f"Total Internet Gateways: {len(internet_gateways)} for {region}")

        load_internet_gateways(neo4j_session, internet_gateways, region, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
    toc = time.perf_counter()
    logger.info(f"Time to process EC2 Internet Gateways: {toc - tic:0.4f} seconds")
