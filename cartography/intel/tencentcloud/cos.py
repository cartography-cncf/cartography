"""Cloud Object Storage (COS) buckets.

COS is not part of Tencent Cloud API 3.0: it exposes an S3-style XML API with its own
request signature. Its Python SDK pins `requests<=2.27.1`, which conflicts with
Cartography, so the two read-only calls this module needs are signed here directly.
See https://www.tencentcloud.com/document/product/436/7778 for the signature.
"""

import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import quote

import neo4j
import requests
import xmltodict
from tencentcloud.common.credential import Credential

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.tencentcloud.cos_bucket import TencentCloudCOSBucketSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

COS_SERVICE_HOST = "service.cos.myqcloud.com"
# Grantee URI COS uses for "everyone, including anonymous users".
ALL_USERS_GRANTEE_URI = "http://cam.qcloud.com/groups/global/AllUsers"

_SIGNATURE_TTL_SECONDS = 600
_TIMEOUT = (60, 60)


def _encode(value: str) -> str:
    return quote(value, safe="-_.~")


def sign_request(
    credential: Credential,
    method: str,
    path: str,
    params: dict[str, str],
    headers: dict[str, str],
    now: int | None = None,
) -> str:
    """Return the COS `Authorization` header value for one request."""
    now = int(time.time()) if now is None else now
    # Start the validity window a minute early to tolerate clock skew, as the COS SDK does.
    key_time = f"{now - 60};{now + _SIGNATURE_TTL_SECONDS}"
    sign_key = hmac.new(
        credential.secret_key.encode(),
        key_time.encode(),
        hashlib.sha1,
    ).hexdigest()
    encoded_params = sorted(
        (_encode(key).lower(), _encode(value)) for key, value in params.items()
    )
    encoded_headers = sorted(
        (_encode(key).lower(), _encode(value)) for key, value in headers.items()
    )
    http_string = "\n".join(
        [
            method.lower(),
            path,
            "&".join(f"{key}={value}" for key, value in encoded_params),
            "&".join(f"{key}={value}" for key, value in encoded_headers),
            "",
        ],
    )
    string_to_sign = "\n".join(
        [
            "sha1",
            key_time,
            hashlib.sha1(http_string.encode()).hexdigest(),
            "",
        ],
    )
    signature = hmac.new(
        sign_key.encode(),
        string_to_sign.encode(),
        hashlib.sha1,
    ).hexdigest()
    return "&".join(
        [
            "q-sign-algorithm=sha1",
            f"q-ak={credential.secret_id}",
            f"q-sign-time={key_time}",
            f"q-key-time={key_time}",
            f"q-header-list={';'.join(key for key, _ in encoded_headers)}",
            f"q-url-param-list={';'.join(key for key, _ in encoded_params)}",
            f"q-signature={signature}",
        ],
    )


def _cos_get(
    credential: Credential,
    host: str,
    params: dict[str, str],
) -> requests.Response:
    signed_headers = {"host": host}
    headers = {
        "Authorization": sign_request(credential, "GET", "/", params, signed_headers),
    }
    if credential.token:
        headers["x-cos-security-token"] = credential.token
    return requests.get(
        f"https://{host}/",
        params=params,
        headers=headers,
        timeout=_TIMEOUT,
    )


@timeit
def get_buckets(credential: Credential) -> list[dict[str, Any]]:
    """List every bucket the account owns, across all regions (GET Service)."""
    buckets: list[dict[str, Any]] = []
    params: dict[str, str] = {}
    while True:
        response = _cos_get(credential, COS_SERVICE_HOST, params)
        response.raise_for_status()
        result = xmltodict.parse(response.content, force_list=("Bucket",))[
            "ListAllMyBucketsResult"
        ]
        buckets.extend((result.get("Buckets") or {}).get("Bucket") or [])
        if str(result.get("IsTruncated")).lower() != "true":
            return buckets
        params = {"marker": result["NextMarker"]}


@timeit
def get_bucket_acl(credential: Credential, bucket: dict[str, Any]) -> dict | None:
    """Return a bucket's ACL, or None when the credential may not read it."""
    host = f"{bucket['Name']}.cos.{bucket['Location']}.myqcloud.com"
    response = _cos_get(credential, host, {"acl": ""})
    if response.status_code in (403, 404):
        # Bucket policies can deny ACL reads even to a read-only principal, and buckets
        # can be deleted between listing and this call. Report and keep going, like the
        # AWS S3 sync does for per-bucket details.
        logger.warning(
            "Could not read the ACL of Tencent Cloud COS bucket %s (HTTP %d); "
            "its anonymous_access will be unset.",
            bucket["Name"],
            response.status_code,
        )
        return None
    response.raise_for_status()
    return xmltodict.parse(response.content, force_list=("Grant",))[
        "AccessControlPolicy"
    ]


def _anonymous_actions(acl: dict[str, Any]) -> list[str]:
    grants = (acl.get("AccessControlList") or {}).get("Grant") or []
    return sorted(
        {
            grant["Permission"]
            for grant in grants
            if (grant.get("Grantee") or {}).get("URI") == ALL_USERS_GRANTEE_URI
        },
    )


def transform(
    raw_buckets: list[dict[str, Any]],
    acls: dict[str, dict | None],
) -> list[dict[str, Any]]:
    buckets = []
    for bucket in raw_buckets:
        acl = acls.get(bucket["Name"])
        anonymous_actions = _anonymous_actions(acl) if acl is not None else None
        buckets.append(
            {
                "id": bucket["Name"],
                "name": bucket["Name"],
                "region": bucket.get("Location"),
                "bucket_type": bucket.get("BucketType"),
                "creation_date": bucket.get("CreationDate"),
                "anonymous_access": (
                    bool(anonymous_actions) if anonymous_actions is not None else None
                ),
                "anonymous_actions": anonymous_actions or None,
            },
        )
    return buckets


@timeit
def load_buckets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Tencent Cloud COS buckets for account %s.",
        len(data),
        account_id,
    )
    load(
        neo4j_session,
        TencentCloudCOSBucketSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        TencentCloudCOSBucketSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credential: Credential,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Sync COS buckets. COS lists buckets globally, so this ignores the region filter."""
    raw_buckets = get_buckets(credential)
    acls = {
        bucket["Name"]: get_bucket_acl(credential, bucket) for bucket in raw_buckets
    }
    load_buckets(neo4j_session, transform(raw_buckets, acls), account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
