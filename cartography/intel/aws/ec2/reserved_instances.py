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


@timeit
def load_reserved_instances(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_reserved_instances = """
    UNWIND $reserved_instances_list as res
        MERGE (ri:EC2ReservedInstance{id: res.ReservedInstancesId})
        ON CREATE SET ri.firstseen = timestamp()
        SET ri.lastupdated = $update_tag, ri.availabilityzone = res.AvailabilityZone, ri.duration = res.Duration,
        ri.end = res.End, ri.start = res.Start, ri.count = res.InstanceCount, ri.type = res.InstanceType,
        ri.productdescription = res.ProductDescription, ri.state = res.State, ri.currencycode = res.CurrencyCode,
        ri.instancetenancy = res.InstanceTenancy, ri.offeringclass = res.OfferingClass,
        ri.offeringtype = res.OfferingType, ri.scope = res.Scope, ri.fixedprice = res.FixedPrice, ri.region=$Region
        WITH ri
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(ri)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    for r_instance in data:
        r_instance["Start"] = str(r_instance["Start"])
        r_instance["End"] = str(r_instance["End"])

    run_write_query(
        neo4j_session,
        ingest_reserved_instances,
        reserved_instances_list=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


@timeit
def cleanup_reserved_instances(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    run_cleanup_job(
        "aws_import_reserved_instances_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


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
        load_reserved_instances(
            neo4j_session,
            data,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_reserved_instances(neo4j_session, common_job_parameters)
