import asyncio
import json
import logging

import httpx
from botocore.exceptions import ClientError
from types_aiobotocore_ecr import ECRClient

logger = logging.getLogger(__name__)


class ECRFetchTransientError(Exception):
    """Raised when a transient ECR/blob fetch failure should skip one artifact."""


ECR_DOCKER_INDEX_MT = "application/vnd.docker.distribution.manifest.list.v2+json"
ECR_DOCKER_MANIFEST_MT = "application/vnd.docker.distribution.manifest.v2+json"
ECR_OCI_INDEX_MT = "application/vnd.oci.image.index.v1+json"
ECR_OCI_MANIFEST_MT = "application/vnd.oci.image.manifest.v1+json"

ALL_ACCEPTED = [
    ECR_OCI_INDEX_MT,
    ECR_DOCKER_INDEX_MT,
    ECR_OCI_MANIFEST_MT,
    ECR_DOCKER_MANIFEST_MT,
]

INDEX_MEDIA_TYPES = {ECR_OCI_INDEX_MT, ECR_DOCKER_INDEX_MT}
INDEX_MEDIA_TYPES_LOWER = {mt.lower() for mt in INDEX_MEDIA_TYPES}

RETRYABLE_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}
RETRYABLE_ECR_ERROR_CODES = {
    "InternalFailure",
    "InternalServerException",
    "RequestLimitExceeded",
    "RequestThrottled",
    "RequestTimeout",
    "RequestTimeoutException",
    "ServerException",
    "ServiceUnavailable",
    "ServiceUnavailableException",
    "Throttling",
    "ThrottlingException",
    "TooManyRequestsException",
}
RETRYABLE_HTTPX_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.PoolTimeout,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
    httpx.TimeoutException,
    httpx.WriteError,
    httpx.WriteTimeout,
)
MAX_BLOB_DOWNLOAD_ATTEMPTS = 3


def is_retryable_aws_client_error(error: ClientError) -> bool:
    error_code = error.response.get("Error", {}).get("Code", "")
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return (
        error_code in RETRYABLE_ECR_ERROR_CODES
        or status_code in RETRYABLE_HTTP_STATUS_CODES
    )


def is_retryable_http_error(error: httpx.HTTPError) -> bool:
    if isinstance(error, RETRYABLE_HTTPX_EXCEPTIONS):
        return True
    if isinstance(error, httpx.HTTPStatusError) and error.response is not None:
        return error.response.status_code in RETRYABLE_HTTP_STATUS_CODES
    return False


def safe_http_error_for_log(error: httpx.HTTPError) -> str:
    if isinstance(error, httpx.HTTPStatusError) and error.response is not None:
        return f"{error.__class__.__name__}(status_code={error.response.status_code})"
    return f"{error.__class__.__name__}: {error}"


async def batch_get_manifest(
    ecr_client: ECRClient,
    repo: str,
    image_ref: str,
    accepted_media_types: list[str],
) -> tuple[dict, str]:
    """Get an image manifest using the ECR BatchGetImage API."""
    try:
        resp = await ecr_client.batch_get_image(
            repositoryName=repo,
            imageIds=(
                [{"imageDigest": image_ref}]
                if image_ref.startswith("sha256:")
                else [{"imageTag": image_ref}]
            ),
            acceptedMediaTypes=accepted_media_types,
        )
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code", "")
        if error_code == "ImageNotFoundException":
            logger.warning(
                "Image %s:%s not found while fetching manifest", repo, image_ref
            )
            return {}, ""
        if error_code in {"AccessDenied", "AccessDeniedException"}:
            logger.warning(
                "Skipping manifest fetch for %s:%s due to %s (missing ecr:BatchGetImage permission)",
                repo,
                image_ref,
                error_code,
            )
            return {}, ""
        if is_retryable_aws_client_error(error):
            logger.warning(
                "Transient AWS error fetching manifest for %s:%s: %s",
                repo,
                image_ref,
                error_code or error,
            )
            raise ECRFetchTransientError(
                f"Transient manifest fetch failure for {repo}:{image_ref}"
            ) from error
        logger.error(
            "Failed to get manifest for %s:%s due to AWS error %s",
            repo,
            image_ref,
            error_code,
        )
        raise
    except Exception:
        logger.exception(
            "Unexpected error fetching manifest for %s:%s", repo, image_ref
        )
        raise

    if not resp.get("images"):
        logger.warning("No image found for %s:%s", repo, image_ref)
        return {}, ""

    manifest_json = json.loads(resp["images"][0]["imageManifest"])
    media_type = resp["images"][0].get("imageManifestMediaType", "")
    return manifest_json, media_type


async def get_blob_json_via_presigned(
    ecr_client: ECRClient,
    repo: str,
    digest: str,
    http_client: httpx.AsyncClient,
) -> dict:
    """Download and parse a JSON blob using a presigned layer URL."""
    try:
        url_response = await ecr_client.get_download_url_for_layer(
            repositoryName=repo,
            layerDigest=digest,
        )
    except ClientError as error:
        if is_retryable_aws_client_error(error):
            logger.warning(
                "Transient AWS error requesting blob download URL for layer %s in repo %s: %s",
                digest,
                repo,
                error.response.get("Error", {}).get("Code", "unknown"),
            )
            raise ECRFetchTransientError(
                f"Transient download URL failure for {repo}@{digest}"
            ) from error
        logger.error(
            "Failed to request download URL for layer %s in repo %s: %s",
            digest,
            repo,
            error.response.get("Error", {}).get("Code", "unknown"),
        )
        raise

    url = url_response["downloadUrl"]
    last_error: httpx.HTTPError | None = None
    for attempt in range(1, MAX_BLOB_DOWNLOAD_ATTEMPTS + 1):
        try:
            response = await http_client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as error:
            last_error = error
            if attempt < MAX_BLOB_DOWNLOAD_ATTEMPTS and is_retryable_http_error(error):
                logger.warning(
                    "Retrying blob download for %s in repo %s after transient HTTP error on attempt %d/%d: %s",
                    digest,
                    repo,
                    attempt,
                    MAX_BLOB_DOWNLOAD_ATTEMPTS,
                    safe_http_error_for_log(error),
                )
                await asyncio.sleep(2 ** (attempt - 1))
                continue
            if is_retryable_http_error(error):
                logger.warning(
                    "Exhausted blob download retries for %s in repo %s after transient HTTP error: %s",
                    digest,
                    repo,
                    safe_http_error_for_log(error),
                )
                raise ECRFetchTransientError(
                    f"Transient blob download failure for {repo}@{digest}"
                ) from error
            logger.error(
                "HTTP error downloading blob %s for repo %s: %s",
                digest,
                repo,
                safe_http_error_for_log(error),
            )
            raise

    raise ECRFetchTransientError(
        f"Transient blob download failure for {repo}@{digest}"
    ) from last_error
