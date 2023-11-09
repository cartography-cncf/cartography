from typing import Optional


def build_arn(
        resource: str,
        account: str,
        typename: str,
        name: str,
        region: Optional[str] = None,
        partition: Optional[str] = None,
) -> str:
    if not partition:
        # TODO: support partitions from others. Please file an issue on this if needed, would love to hear from you
        partition = 'aws'
    if not region:
        # Some resources are present in all regions, e.g. IAM policies
        region = ""
    return f"arn:{partition}:{resource}:{region}:{account}:{typename}/{name}"
