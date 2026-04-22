import logging
from typing import Set
from typing import Tuple

from botocore.exceptions import UnknownRegionError

logger = logging.getLogger(__name__)


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
