import logging

import boto3
from botocore.exceptions import UnknownRegionError

logger = logging.getLogger(__name__)


def filter_regions_to_supported_service_regions(
    boto3_session: boto3.session.Session,
    service_name: str,
    regions: list[str],
) -> tuple[list[str], list[str]]:
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

    partitions: set[str] = set()
    for region in regions:
        try:
            partitions.add(boto3_session.get_partition_for_region(region))
        except UnknownRegionError:
            logger.debug(
                "Could not determine AWS partition for region '%s' while filtering service '%s' regions.",
                region,
                service_name,
            )

    if not partitions:
        partitions.update(boto3_session.get_available_partitions())

    available_regions: set[str] = set()
    for partition_name in partitions:
        available_regions.update(
            boto3_session.get_available_regions(
                service_name,
                partition_name=partition_name,
            )
        )

    if not available_regions:
        logger.warning(
            "Could not determine available %s regions. Continuing with requested regions.",
            service_name,
        )
        return regions, []

    filtered_regions = [region for region in regions if region in available_regions]
    unsupported_regions = [
        region for region in regions if region not in available_regions
    ]
    return filtered_regions, unsupported_regions
