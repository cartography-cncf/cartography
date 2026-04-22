import logging
from typing import List
from typing import Set
from typing import Tuple

from botocore.exceptions import UnknownRegionError

logger = logging.getLogger(__name__)


def parse_and_validate_aws_requested_syncs(aws_requested_syncs: str) -> List[str]:
    from cartography.intel.aws.resources import RESOURCE_FUNCTIONS

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


def filter_regions_to_supported_service_regions(
    boto3_session: object,
    service_name: str,
    regions: list[str],
) -> Tuple[list[str], list[str]]:
    """
    Filter candidate regions to the subset with known service endpoints.

    Returns a tuple of:
    - filtered regions supported by the service
    - candidate regions skipped as unsupported for the service

    If service endpoint metadata cannot produce a usable subset, fall back to the
    original candidate regions and report no skipped regions.
    """
    if not regions:
        return [], []

    partitions: Set[str] = set()
    get_partition_for_region = getattr(boto3_session, "get_partition_for_region", None)
    if callable(get_partition_for_region):
        for region in regions:
            try:
                partitions.add(get_partition_for_region(region))
            except UnknownRegionError:
                logger.debug(
                    "Could not determine AWS partition for region '%s' while filtering service '%s' regions.",
                    region,
                    service_name,
                )

    if not partitions:
        get_available_partitions = getattr(
            boto3_session,
            "get_available_partitions",
            None,
        )
        if callable(get_available_partitions):
            partitions.update(get_available_partitions())

    available_regions: Set[str] = set()
    get_available_regions = getattr(boto3_session, "get_available_regions", None)
    if callable(get_available_regions):
        for partition_name in partitions:
            available_regions.update(
                get_available_regions(
                    service_name,
                    partition_name=partition_name,
                )
            )

    if not available_regions:
        return regions, []

    filtered_regions = [region for region in regions if region in available_regions]
    unsupported_regions = [
        region for region in regions if region not in available_regions
    ]
    return filtered_regions, unsupported_regions
