import logging
from typing import List

import boto3

from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_ec2_regions(boto3_session: boto3.session.Session) -> List[str]:
    client = create_boto3_client(boto3_session, "ec2")
    result = client.describe_regions()
    return [r["RegionName"] for r in result["Regions"]]
