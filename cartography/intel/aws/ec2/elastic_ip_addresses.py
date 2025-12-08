import logging
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError

from cartography.client.core.tx import run_write_query
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
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
    ingest_addresses = """
    UNWIND $elastic_ip_addresses as eia
        MERGE (address: ElasticIPAddress{id: eia.PublicIp})
        ON CREATE SET address.firstseen = timestamp()
        SET address.instance_id = eia.InstanceId, address.public_ip = eia.PublicIp,
        address.allocation_id = eia.AllocationId, address.association_id = eia.AssociationId,
        address.domain = eia.Domain, address.network_interface_id = eia.NetworkInterfaceId,
        address.network_interface_owner_id = eia.NetworkInterfaceOwnerId,
        address.private_ip_address = eia.PrivateIpAddress, address.public_ipv4_pool = eia.PublicIpv4Pool,
        address.network_border_group = eia.NetworkBorderGroup, address.customer_owned_ip = eia.CustomerOwnedIp,
        address.customer_owned_ipv4_pool = eia.CustomerOwnedIpv4Pool, address.carrier_ip = eia.CarrierIp,
        address.region = $Region, address.lastupdated = $update_tag
        WITH address

        MATCH (account:AWSAccount{id: $aws_account_id})
        MERGE (account)-[r:RESOURCE]->(address)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH address

        MATCH (instance:EC2Instance) WHERE instance.id = address.instance_id
        MERGE (instance)-[r:ELASTIC_IP_ADDRESS]->(address)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH address

        MATCH (ni:NetworkInterface{id: address.network_interface_id})
        MERGE (ni)-[r:ELASTIC_IP_ADDRESS]->(address)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    run_write_query(
        neo4j_session,
        ingest_addresses,
        elastic_ip_addresses=elastic_ip_addresses,
        Region=region,
        aws_account_id=current_aws_account_id,
        update_tag=update_tag,
    )


@timeit
def cleanup_elastic_ip_addresses(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    run_cleanup_job(
        "aws_import_elastic_ip_addresses_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


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
