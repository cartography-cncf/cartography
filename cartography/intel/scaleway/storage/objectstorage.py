import json
import logging
from typing import Any

import boto3
import neo4j
import scaleway
from botocore.exceptions import ClientError
from policyuniverse.policy import Policy

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.scaleway.utils import DEFAULT_REGIONS
from cartography.models.scaleway.storage.objectstorage import (
    ScalewayObjectStorageBucketSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Canned S3 group URIs that expose a bucket to everyone on the internet.
PUBLIC_ACL_URIS = {
    "http://acs.amazonaws.com/groups/global/AllUsers",
    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers",
}

# Sentinel for a detail call that could not be read (e.g. AccessDenied): the
# state is unknown, which must NOT be collapsed into a "not public" signal.
FETCH_FAILED = "__FETCH_FAILED__"

# Error codes that mean the config genuinely does not exist (a real "absent"
# answer, distinct from a read failure).
_ABSENT_ERROR_CODES = {
    "NoSuchBucketPolicy",
    "NoSuchTagSet",
    "NoSuchConfiguration",
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: dict[str, Any],
    org_id: str,
    projects_id: list[str],
    update_tag: int,
) -> None:
    buckets, complete_projects = get(client, projects_id)
    buckets_by_project = transform_buckets(buckets)
    load_buckets(neo4j_session, buckets_by_project, update_tag)
    # Only clean projects we fully enumerated: a project whose listing failed in
    # any region has an incomplete view, so cleaning it would delete
    # last-known-good buckets that simply weren't (re)listed this run.
    cleanup(neo4j_session, complete_projects, common_job_parameters)


@timeit
def get(
    client: scaleway.Client, projects_id: list[str]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Scaleway Object Storage is S3-compatible and is not exposed by the
    Scaleway Python SDK, so we use boto3 against the regional S3 endpoints.

    S3 calls are scoped to the access key's preferred Project unless the key is
    suffixed with ``@<project_id>``, so we iterate every project explicitly to
    cover multi-project orgs (and to keep ingestion aligned with cleanup).

    Returns the discovered buckets and the list of projects that were fully
    enumerated (every region listed without error) and are therefore safe to
    clean up."""
    buckets: list[dict[str, Any]] = []
    complete_projects: list[str] = []
    for project_id in projects_id:
        project_complete = True
        for region in DEFAULT_REGIONS:
            s3 = boto3.client(
                "s3",
                region_name=region,
                endpoint_url=f"https://s3.{region}.scw.cloud",
                aws_access_key_id=f"{client.access_key}@{project_id}",
                aws_secret_access_key=client.secret_key,
            )
            try:
                listing = s3.list_buckets()
            except ClientError as e:
                # Don't let one region/project abort the whole Scaleway sync,
                # but mark the project incomplete so cleanup skips it.
                logger.warning(
                    "Could not list Scaleway buckets in project '%s' region '%s': %s",
                    project_id,
                    region,
                    e.response.get("Error", {}).get("Code"),
                )
                project_complete = False
                continue
            for bucket in listing.get("Buckets", []):
                buckets.append(_get_bucket_details(s3, bucket, region, project_id))
        if project_complete:
            complete_projects.append(project_id)
    return buckets, complete_projects


def _get_bucket_details(
    s3: Any, bucket: dict[str, Any], region: str, project_id: str
) -> dict[str, Any]:
    name = bucket["Name"]
    details: dict[str, Any] = {
        "name": name,
        "region": region,
        "endpoint": f"https://{name}.s3.{region}.scw.cloud",
        "creation_date": bucket.get("CreationDate"),
        "project_id": project_id,
        "acl": None,
        "policy": None,
        "versioning": None,
        "tags": None,
    }
    # Each call is independent: a bucket policy can lock the owner out of the
    # admin endpoints (AccessDenied), so we keep whatever we can read.
    details["acl"] = _safe_call(s3.get_bucket_acl, name)
    details["policy"] = _safe_call(s3.get_bucket_policy, name)
    details["versioning"] = _safe_call(s3.get_bucket_versioning, name)
    details["tags"] = _safe_call(s3.get_bucket_tagging, name)
    return details


def _safe_call(func: Any, name: str) -> Any:
    """Returns the response, None if the config is genuinely absent, or
    FETCH_FAILED if the call could not be read (so callers can keep the state
    unknown instead of assuming a benign default)."""
    try:
        return func(Bucket=name)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        logger.debug(
            "Scaleway Object Storage %s on bucket '%s' failed: %s",
            func.__name__,
            name,
            code,
        )
        return None if code in _ABSENT_ERROR_CODES else FETCH_FAILED


def transform_buckets(
    buckets: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for bucket in buckets:
        project_id = bucket["project_id"]
        # Leave the exposure signals null (unknown) when their source read
        # failed, rather than reporting a bucket as not-public on bad data.
        acl = bucket["acl"]
        acl_public = None if acl is FETCH_FAILED else _is_acl_public(acl)
        policy = bucket["policy"]
        if policy is FETCH_FAILED:
            anonymous_access, anonymous_actions = None, None
        else:
            anonymous_access, anonymous_actions = _parse_policy(policy)
        versioning = bucket["versioning"]
        formatted = {
            "id": bucket["name"],
            "name": bucket["name"],
            "region": bucket["region"],
            "endpoint": bucket["endpoint"],
            "creation_date": bucket["creation_date"],
            "tags": (
                None if bucket["tags"] is FETCH_FAILED else _format_tags(bucket["tags"])
            ),
            "versioning_status": (
                None
                if versioning in (None, FETCH_FAILED)
                else (versioning.get("Status") or None)
            ),
            "acl_public": acl_public,
            "anonymous_access": anonymous_access,
            "anonymous_actions": anonymous_actions,
            # Tri-state combined public signal: True/False when known, None when
            # both sources were unreadable (so "unknown" is not reported as safe).
            "public": _combine_public(acl_public, anonymous_access),
        }
        result.setdefault(project_id, []).append(formatted)
    return result


def _combine_public(
    acl_public: bool | None, anonymous_access: bool | None
) -> bool | None:
    known = [v for v in (acl_public, anonymous_access) if v is not None]
    if not known:
        return None
    return any(known)


def _format_tags(tagging: dict[str, Any] | None) -> list[str] | None:
    if not tagging:
        return None
    tags = [f"{t['Key']}={t['Value']}" for t in tagging.get("TagSet", [])]
    return tags or None


def _is_acl_public(acl: dict[str, Any] | None) -> bool:
    if not acl:
        return False
    for grant in acl.get("Grants", []):
        grantee = grant.get("Grantee", {})
        if grantee.get("Type") == "Group" and grantee.get("URI") in PUBLIC_ACL_URIS:
            return True
    return False


def _parse_policy(policy: dict[str, Any] | None) -> tuple[bool, list[str]]:
    """Reuse policyuniverse (as the AWS S3 module does) to detect anonymous
    access from an S3-compatible bucket policy."""
    if not policy:
        return False, []
    parsed = Policy(json.loads(policy["Policy"]))
    if parsed.is_internet_accessible():
        return True, sorted(parsed.internet_accessible_actions())
    return False, []


@timeit
def load_buckets(
    neo4j_session: neo4j.Session,
    data: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, buckets in data.items():
        logger.info(
            "Loading %d Scaleway ObjectStorageBuckets in project '%s' into Neo4j.",
            len(buckets),
            project_id,
        )
        load(
            neo4j_session,
            ScalewayObjectStorageBucketSchema(),
            buckets,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_id: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in projects_id:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            ScalewayObjectStorageBucketSchema(), scoped_job_parameters
        ).run(neo4j_session)
