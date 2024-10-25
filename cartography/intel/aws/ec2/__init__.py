import logging
from typing import List

import boto3

from cartography.intel.aws.util.boto3 import get_botocore_config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_ec2_regions(boto3_session: boto3.session.Session) -> List[str]:
    client = boto3_session.client('ec2', config=get_botocore_config())
    result = client.describe_regions()
    return [r['RegionName'] for r in result['Regions']]
