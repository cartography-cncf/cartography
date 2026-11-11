import logging
from collections.abc import Callable
from typing import Any

from tencentcloud.common.common_client import CommonClient
from tencentcloud.common.credential import Credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.retry import StandardRetryer

logger = logging.getLogger(__name__)

# Tencent Cloud API 3.0 versions of the products this module reads. Every call goes
# through the SDK's CommonClient, so only `tencentcloud-sdk-python-common` is needed.
API_VERSIONS = {
    "cam": "2019-01-16",
    "cbs": "2017-03-12",
    "clb": "2018-03-17",
    "cvm": "2017-03-12",
    "vpc": "2017-03-12",
}

_REQUEST_TIMEOUT_SECONDS = 60
_MAX_ATTEMPTS = 5

# Error codes returned when a product is not deployed in the requested region. Those
# regions are skipped; every other error propagates.
_REGION_UNAVAILABLE_ERROR_CODES = frozenset(
    {
        "UnsupportedRegion",
        "InvalidParameterValue.UnsupportedRegion",
        "UnsupportedOperation.UnsupportedRegion",
    },
)


def build_credential(secret_id: str, secret_key: str) -> Credential:
    return Credential(secret_id, secret_key)


def build_client(credential: Credential, service: str, region: str = "") -> Any:
    """Build a CommonClient for one Tencent Cloud product in one region.

    Global products such as CAM take an empty region.
    """
    profile = ClientProfile(
        httpProfile=HttpProfile(reqTimeout=_REQUEST_TIMEOUT_SECONDS),
        language="en-US",
        retryer=StandardRetryer(max_attempts=_MAX_ATTEMPTS, logger=logger),
    )
    return CommonClient(service, API_VERSIONS[service], credential, region, profile)


def call(client: Any, action: str, params: dict[str, Any] | None = None) -> dict:
    """Call one API action and return the body of its `Response` envelope."""
    return client.call_json(action, params or {})["Response"]


def paginate_offset(
    client: Any,
    action: str,
    list_key: str,
    params: dict[str, Any] | None = None,
    limit: int = 100,
    string_paging: bool = False,
) -> list[dict[str, Any]]:
    """Read every page of an Offset/Limit paginated action.

    VPC actions type `Offset` and `Limit` as strings; set `string_paging` for those.
    """
    items: list[dict[str, Any]] = []
    offset = 0
    while True:
        page_params = dict(params or {})
        page_params["Offset"] = str(offset) if string_paging else offset
        page_params["Limit"] = str(limit) if string_paging else limit
        response = call(client, action, page_params)
        # Empty result sets can come back as null rather than [].
        page = response.get(list_key) or []
        items.extend(page)
        offset += len(page)
        if not page or offset >= response["TotalCount"]:
            return items


def paginate_page(
    client: Any,
    action: str,
    list_key: str,
    params: dict[str, Any] | None = None,
    rp: int = 200,
) -> list[dict[str, Any]]:
    """Read every page of a CAM-style Page/Rp paginated action."""
    items: list[dict[str, Any]] = []
    page_number = 1
    while True:
        page_params = dict(params or {})
        page_params["Page"] = page_number
        page_params["Rp"] = rp
        response = call(client, action, page_params)
        page = response.get(list_key) or []
        items.extend(page)
        if not page or len(items) >= response["TotalNum"]:
            return items
        page_number += 1


def get_regions(credential: Credential) -> list[str]:
    """Return every CVM region the account can use."""
    client = build_client(credential, "cvm")
    response = call(client, "DescribeRegions")
    return sorted(
        region["Region"]
        for region in response["RegionSet"]
        if region["RegionState"] == "AVAILABLE"
    )


def is_region_unavailable(exc: TencentCloudSDKException) -> bool:
    return exc.get_code() in _REGION_UNAVAILABLE_ERROR_CODES


def get_in_region(
    credential: Credential,
    service: str,
    region: str,
    fetch: Callable[[Any], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Run `fetch` against one region's client.

    Regions where the product is not deployed return an empty list; every other error
    propagates so that a partial read never triggers cleanup.
    """
    client = build_client(credential, service, region)
    try:
        return fetch(client)
    except TencentCloudSDKException as exc:
        if not is_region_unavailable(exc):
            raise
        logger.info(
            "Tencent Cloud %s is not available in region %s, skipping.",
            service,
            region,
        )
        return []


def format_tags(
    tags: list[dict[str, Any]] | None,
    key_field: str = "Key",
    value_field: str = "Value",
) -> list[str] | None:
    """Flatten Tencent Cloud key/value tags to `key:value` strings."""
    if not tags:
        return None
    return [f"{tag[key_field]}:{tag[value_field]}" for tag in tags]
