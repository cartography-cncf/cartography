import logging
from typing import List

from cartography.intel.aws.resources import RESOURCE_FUNCTIONS

logger = logging.getLogger(__name__)


def parse_and_validate_aws_requested_syncs(aws_requested_syncs: str) -> List[str]:
    validated_resources: List[str] = []
    for resource in aws_requested_syncs.split(","):
        resource = resource.strip()

        if resource in RESOURCE_FUNCTIONS:
            validated_resources.append(resource)
        else:
            valid_syncs: str = ", ".join(RESOURCE_FUNCTIONS.keys())
            raise ValueError(
                f'Error parsing `aws-requested-syncs`. You specified "{aws_requested_syncs}". '
                f"Please check that your string is formatted properly. "
                f'Example valid input looks like "s3,iam,rds" or "s3, ec2:instance, dynamodb". '
                f"Our full list of valid values is: {valid_syncs}.",
            )
    return validated_resources


def parse_and_validate_aws_regions(aws_regions: str) -> list[str]:
    """
    Parse and validate a comma-separated string of AWS regions.
    :param aws_regions: Comma-separated string of AWS regions
    :return: A validated list of AWS regions
    """
    validated_regions: List[str] = []
    for region in aws_regions.split(","):
        region = region.strip()
        if region:
            validated_regions.append(region)
        else:
            logger.warning(
                f'Unable to parse string "{region}". Please check the value you passed to `aws-regions`. '
                f'You specified "{aws_regions}". Continuing on with sync.',
            )

    if not validated_regions:
        raise ValueError(
            f'`aws-regions` was set but no regions were specified. You provided this string: "{aws_regions}"',
        )
    return validated_regions
