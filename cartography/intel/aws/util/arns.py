from functools import lru_cache
from typing import Optional

import botocore.session
from botocore.exceptions import UnknownRegionError


@lru_cache(maxsize=None)
def get_partition(region: str) -> str:
    """
    Return the AWS partition that contains the region: "aws" for commercial
    regions, "aws-us-gov" for GovCloud (US) and "aws-cn" for China.

    Synthesized ARNs must use it to match the ARNs that AWS returns. The value
    comes from botocore's bundled endpoint data, so the lookup needs no
    credentials and makes no API call. A FIPS pseudo-region such as
    "fips-us-gov-west-1" is in the partition of its base region, as botocore
    resolves it. A region that botocore does not know resolves to "aws", which
    is also the partition botocore uses for its endpoints.
    """
    region = region.replace("fips-", "").replace("-fips", "")
    try:
        return botocore.session.get_session().get_partition_for_region(region)
    except UnknownRegionError:
        return "aws"


def get_account_partition(regions: list[str], fallback_region: str | None) -> str:
    """
    Return the partition for an account-level ARN, such as an S3 bucket or the root principal.

    It is the partition of the first region to sync. When region discovery found no region, it
    falls back to the session's region, and then to "aws", the partition botocore uses then.
    """
    region = regions[0] if regions else fallback_region
    return get_partition(region) if region else "aws"


def build_arn(
    resource: str,
    account: str,
    typename: str,
    name: str,
    region: Optional[str] = None,
    partition: Optional[str] = None,
) -> str:
    if not partition:
        partition = "aws"
    if not region:
        # Some resources are present in all regions, e.g. IAM policies
        region = ""
    return f"arn:{partition}:{resource}:{region}:{account}:{typename}/{name}"
