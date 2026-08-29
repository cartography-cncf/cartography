import logging
from functools import wraps
from typing import Any
from typing import Callable
from typing import cast
from typing import Iterable
from typing import Optional
from typing import TypeVar

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectionClosedError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ReadTimeoutError
from botocore.parsers import ResponseParserError

from cartography.util import is_aws_region_skippable_client_error
from cartography.util import timeit

logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}
AWSGetFunc = TypeVar("AWSGetFunc", bound=Callable[..., Iterable[Any]])


class SageMakerTransientRegionFailure(Exception):
    pass


def _is_retryable_sagemaker_error(error: ClientError) -> bool:
    error_code = error.response.get("Error", {}).get("Code", "")
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return (
        error_code
        in {
            "RequestLimitExceeded",
            "RequestThrottled",
            "RequestTimeout",
            "RequestTimeoutException",
            "ServiceUnavailable",
            "ServiceUnavailableException",
            "Throttling",
            "ThrottlingException",
            "TooManyRequestsException",
        }
        or status_code in _RETRYABLE_HTTP_STATUS_CODES
    )


def sagemaker_handle_regions(func: AWSGetFunc) -> AWSGetFunc:
    @wraps(func)
    def inner_function(*args, **kwargs):  # type: ignore
        try:
            return func(*args, **kwargs)
        except ClientError as error:
            error_code = error.response.get("Error", {}).get("Code")
            error_message = error.response.get("Error", {}).get("Message")
            if error_code == "InvalidToken":
                raise RuntimeError(
                    "AWS returned an InvalidToken error. Configure regional STS endpoints by "
                    "setting environment variable AWS_STS_REGIONAL_ENDPOINTS=regional or adding "
                    "'sts_regional_endpoints = regional' to your AWS config file."
                ) from error
            if _is_retryable_sagemaker_error(error):
                raise SageMakerTransientRegionFailure(
                    f"AWS SDK retries were exhausted for transient SageMaker failure in {func.__name__}"
                ) from error
            if is_aws_region_skippable_client_error(error):
                logger.warning("%s in this region. Skipping...", error_message)
                return []
            raise
        except (
            ConnectionClosedError,
            ConnectTimeoutError,
            EndpointConnectionError,
            ReadTimeoutError,
            ResponseParserError,
        ) as error:
            raise SageMakerTransientRegionFailure(
                f"Encountered a transient regional SageMaker endpoint failure in {func.__name__}"
            ) from error

    return cast(AWSGetFunc, inner_function)


@timeit
def sync_sagemaker_resource(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
    skip_regions: set[str],
    submodule_name: str,
    get_resources: Callable[[boto3.session.Session, str], list[dict[str, Any]]],
    transform_resources: Callable[[list[dict[str, Any]], str], list[dict[str, Any]]],
    load_resources: Callable[
        [neo4j.Session, list[dict[str, Any]], str, str, int],
        None,
    ],
    cleanup_resources: Callable[[neo4j.Session, dict[str, Any]], None],
) -> set[str]:
    cleanup_safe = not skip_regions
    newly_failed_regions: set[str] = set()

    for region in regions:
        if region in skip_regions:
            logger.info(
                "Skipping SageMaker submodule '%s' for account '%s' in region '%s' because the region was previously marked as transiently failed.",
                submodule_name,
                current_aws_account_id,
                region,
            )
            continue

        logger.debug(
            "Syncing SageMaker submodule '%s' for region '%s' in account '%s'.",
            submodule_name,
            region,
            current_aws_account_id,
        )
        try:
            resources = get_resources(boto3_session, region)
        except SageMakerTransientRegionFailure as error:
            newly_failed_regions.add(region)
            cleanup_safe = False
            logger.warning(
                "Marking SageMaker region '%s' as transiently failed for account '%s' in submodule '%s': %s",
                region,
                current_aws_account_id,
                submodule_name,
                error,
            )
            continue

        transformed_resources = transform_resources(resources, region)
        load_resources(
            neo4j_session,
            transformed_resources,
            region,
            current_aws_account_id,
            aws_update_tag,
        )

    if cleanup_safe:
        cleanup_resources(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping SageMaker cleanup for account '%s' in submodule '%s' because one or more regions were transiently skipped. Preserving last-known-good data.",
            current_aws_account_id,
            submodule_name,
        )

    return newly_failed_regions


def extract_bucket_name_from_s3_uri(s3_uri: str) -> Optional[str]:
    """
    Extract bucket name from S3 URI.

    Example: s3://my-bucket/path/to/data -> my-bucket
    """
    if not s3_uri or not s3_uri.startswith("s3://"):
        return None
    # Remove s3:// prefix and split on /
    bucket_name = s3_uri[5:].split("/")[0]
    return bucket_name if bucket_name else None
