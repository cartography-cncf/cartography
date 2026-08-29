import logging
import re
from typing import List

from cartography.intel.aws.resources import RESOURCE_FUNCTIONS

logger = logging.getLogger(__name__)
AWS_ACCOUNT_ID_REGEX = re.compile(r"^\d{12}$")


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


def parse_and_validate_aws_account_ids(account_ids: str) -> list[str]:
    """
    Parse and validate a comma-separated string of AWS account IDs.
    :param account_ids: Comma-separated string of 12-digit AWS account IDs
    :return: A validated list of account IDs
    """
    validated_account_ids: list[str] = []
    for account_id in account_ids.split(","):
        account_id = account_id.strip()
        if not account_id:
            continue
        if not AWS_ACCOUNT_ID_REGEX.match(account_id):
            raise ValueError(
                f'Error parsing AWS account IDs. You specified "{account_ids}". '
                "AWS account IDs must be 12-digit numbers.",
            )
        validated_account_ids.append(account_id)

    if not validated_account_ids:
        raise ValueError(
            f"AWS account ID list was set but no account IDs were specified. You provided this string: {account_ids!r}",
        )
    return validated_account_ids
