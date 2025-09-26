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
        partition = "aws"
    if not region:
        # Some resources are present in all regions, e.g. IAM policies
        region = ""
    return f"arn:{partition}:{resource}:{region}:{account}:{typename}/{name}"


def convert_sts_arn_to_iam_arn(arn: str) -> str:
    """
    Convert STS ARN to the corresponding IAM resource ARN.

    Example:
    arn:aws:sts::123456789012:assumed-role/my-role-name/my-role-session-name
    -> arn:aws:iam::123456789012:role/my-role-name

    arn:aws:iam::123456789012:user/Alice -> arn:aws:iam::123456789012:user/Alice
    """

    if not arn or not arn.startswith("arn:"):
        return arn

    parts = arn.split(":")
    if len(parts) < 6:
        return arn

    service = parts[2]
    account_id = parts[4]
    resource = parts[5]

    if service != "sts" or not resource.startswith("assumed-role/"):
        return arn

    resource_parts = resource.split("/")
    if len(resource_parts) < 2:
        return arn

    role_name = resource_parts[1]
    return build_arn("iam", account_id, "role", role_name)
