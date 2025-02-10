from typing import List

from cartography.intel.aws.resources import RESOURCE_FUNCTIONS


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
