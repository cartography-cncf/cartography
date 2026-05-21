from typing import List

from cartography.intel.oci.resources import RESOURCE_FUNCTIONS


def parse_and_validate_oci_requested_syncs(oci_requested_syncs: str) -> List[str]:
    validated_resources: List[str] = []
    for resource in oci_requested_syncs.split(','):
        resource = resource.strip()

        if resource in RESOURCE_FUNCTIONS:
            validated_resources.append(resource)
        else:
            valid_syncs: str = ', '.join(RESOURCE_FUNCTIONS.keys())
            raise ValueError(
                f'Error parsing `oci-requested-syncs`. You specified "{oci_requested_syncs}". '
                f'Please check that your string is formatted properly. '
                f'Example valid input looks like "iam". '
                f'Our full list of valid values is: {valid_syncs}.',
            )
    return validated_resources
