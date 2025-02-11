import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.ec2.images import EC2ImageSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_images_in_use(neo4j_session: neo4j.Session, region: str, current_aws_account_id: str) -> List[str]:
    get_images_query = """
    MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(i:EC2Instance)
    WHERE i.region = $Region
    RETURN DISTINCT(i.imageid) as image
    UNION
    MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(lc:LaunchConfiguration)
    WHERE lc.region = $Region
    RETURN DISTINCT(lc.image_id) as image
    UNION
    MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(ltv:LaunchTemplateVersion)
    WHERE ltv.region = $Region
    RETURN DISTINCT(ltv.image_id) as image
    """
    results = neo4j_session.run(get_images_query, AWS_ACCOUNT_ID=current_aws_account_id, Region=region)
    images = {r['image'] for r in results if r['image']}
    return list(images)


@timeit
@aws_handle_regions
def get_images(boto3_session: boto3.session.Session, region: str, image_ids: List[str]) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    images = []
    self_images = []
    try:
        self_images = client.describe_images(Owners=['self'])['Images']
    except ClientError as e:
        logger.warning(f"Failed retrieve self owned images for region - {region}. Error - {e}")
    images.extend(self_images)
    if image_ids:
        self_image_ids = {image['ImageId'] for image in images}
        ids_pending = [id for id in image_ids if id not in ids_retrieved]
        # Go one by one to avoid losing all images if one fails
        for image in ids_pending:
            try:
                public_images = client.describe_images(ImageIds=[image])['Images']
                images.extend(public_images)
            except ClientError as e:
                logger.warning(f"Failed retrieve non-self image for region - {region}. Error - {e}")
    return images


@timeit
def load_images(
        neo4j_session: neo4j.Session,
        data: List[Dict[str, Any]],
        region: str,
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    # AMI IDs are unique to each AWS Region. Hence we make an 'ID' string that is a combo of ImageId and region
    for image in data:
        image['ID'] = image['ImageId'] + '|' + region
    load(
        neo4j_session,
        EC2ImageSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_images(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    cleanup_job = GraphJob.from_node_schema(EC2ImageSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


@timeit
def sync_ec2_images(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing images for region '%s' in account '%s'.", region, current_aws_account_id)
        images_in_use = get_images_in_use(neo4j_session, region, current_aws_account_id)
        data = get_images(boto3_session, region, images_in_use)
        load_images(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_images(neo4j_session, common_job_parameters)
