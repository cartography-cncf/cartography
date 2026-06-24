import logging
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.gcp.labels import sync_labels
from cartography.intel.gcp.util import classify_gcp_http_error
from cartography.intel.gcp.util import gcp_api_execute_with_retry
from cartography.intel.gcp.util import is_permission_denied_error
from cartography.intel.gcp.util import summarize_gcp_http_error
from cartography.models.gcp.storage.bucket import GCPBucketLabelSchema
from cartography.models.gcp.storage.bucket import GCPBucketSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_buckets(storage: Resource, project_id: str) -> Dict:
    """
    Returns a list of storage objects within some given project

    :type storage: The GCP storage resource object
    :param storage: The storage resource object created by googleapiclient.discovery.build()

    :type project_id: str
    :param project_id: The Google Project Id that you are retrieving buckets from

    :rtype: Storage Object
    :return: Storage response object
    """
    try:
        # `projection=full` is required to get the `acl` / `defaultObjectAcl`
        # arrays back; the default `noAcl` projection strips them, which would
        # leave legacy-ACL public buckets undetectable. With `full`, the API
        # caps each response at 200 buckets, so we must follow `nextPageToken`
        # before downstream cleanup runs — otherwise projects with more than
        # 200 buckets would lose every bucket beyond the first page.
        items: List[Dict] = []
        first_response: Dict = {}
        req = storage.buckets().list(project=project_id, projection="full")
        while req is not None:
            res = gcp_api_execute_with_retry(req)
            if not first_response:
                first_response = res
            items.extend(res.get("items", []))
            req = storage.buckets().list_next(
                previous_request=req, previous_response=res
            )
        # Preserve the first response's shape (kind, selfLink, ...) and replace
        # items with the fully paginated list so callers see one logical page.
        first_response["items"] = items
        first_response.pop("nextPageToken", None)
        return first_response
    except HttpError as e:
        category = classify_gcp_http_error(e)
        if category == "invalid":
            logger.warning(
                "The project %s is invalid - returned a 400 invalid error. %s",
                project_id,
                summarize_gcp_http_error(e),
            )
            return {}
        elif is_permission_denied_error(e):
            logger.warning(
                "You do not have storage.bucket.list access to the project %s. %s",
                project_id,
                summarize_gcp_http_error(e),
            )
            return {}
        else:
            raise


@timeit
def transform_gcp_buckets_and_labels(bucket_res: Dict) -> Tuple[List[Dict], List[Dict]]:
    """
    Transform the GCP Storage Bucket response object for Neo4j ingestion.

    :param bucket_res: The raw GCP bucket response.
    :return: A tuple of (buckets, bucket_labels) ready for ingestion to Neo4j.
    """

    buckets: List[Dict] = []
    labels: List[Dict] = []
    public_entities = {"allUsers", "allAuthenticatedUsers"}
    for b in bucket_res.get("items", []):
        # Legacy bucket / default-object ACLs can expose a bucket publicly without any
        # IAM binding. Detect either form so the ontology `_ont_public` projection
        # covers buckets that still rely on ACLs (uniformBucketLevelAccess=false).
        acl_public = any(
            entry.get("entity") in public_entities for entry in (b.get("acl") or [])
        ) or any(
            entry.get("entity") in public_entities
            for entry in (b.get("defaultObjectAcl") or [])
        )
        bucket = {
            "iam_config_bucket_policy_only": (
                b.get("iamConfiguration", {}).get("bucketPolicyOnly", {}).get("enabled")
            ),
            "iam_config_public_access_prevention": (
                b.get("iamConfiguration", {}).get("publicAccessPrevention")
            ),
            "id": b["id"],
            # Preserve legacy bucket_id field for compatibility
            "bucket_id": b["id"],
            "owner_entity": b.get("owner", {}).get("entity"),
            "owner_entity_id": b.get("owner", {}).get("entityId"),
            "kind": b.get("kind"),
            "location": b.get("location"),
            "location_type": b.get("locationType"),
            "meta_generation": b.get("metageneration"),
            "project_number": b.get("projectNumber"),
            "self_link": b.get("selfLink"),
            "storage_class": b.get("storageClass"),
            "time_created": b.get("timeCreated"),
            "versioning_enabled": b.get("versioning", {}).get("enabled"),
            "retention_period": b.get("retentionPolicy", {}).get("retentionPeriod"),
            "default_kms_key_name": b.get("encryption", {}).get("defaultKmsKeyName"),
            "log_bucket": b.get("logging", {}).get("logBucket"),
            "requester_pays": b.get("billing", {}).get("requesterPays"),
            "acl_public": acl_public,
        }
        buckets.append(bucket)
        for key, val in b.get("labels", {}).items():
            labels.append(
                {
                    "id": f"GCPBucket_{key}",
                    "key": key,
                    "value": val,
                    "bucket_id": b["id"],
                }
            )
    return buckets, labels


@timeit
def load_gcp_buckets(
    neo4j_session: neo4j.Session,
    buckets: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """Ingest GCP Storage Buckets to Neo4j."""
    load(
        neo4j_session,
        GCPBucketSchema(),
        buckets,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def load_gcp_bucket_labels(
    neo4j_session: neo4j.Session,
    bucket_labels: List[Dict],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """Ingest GCP Storage Bucket labels and attach them to buckets."""
    load(
        neo4j_session,
        GCPBucketLabelSchema(),
        bucket_labels,
        lastupdated=gcp_update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup_gcp_buckets(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """Delete out-of-date GCP Storage Bucket nodes and relationships."""
    # Bucket labels depend on buckets, so we must remove labels first to avoid
    # dangling references before deleting the buckets themselves.
    GraphJob.from_node_schema(GCPBucketLabelSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(GCPBucketSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_gcp_buckets(
    neo4j_session: neo4j.Session,
    storage: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP instances using the Storage resource object, ingest to Neo4j, and clean up old data.

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type storage: The storage resource object created by googleapiclient.discovery.build()
    :param storage: The GCP Storage resource object

    :type project_id: str
    :param project_id: The project ID of the corresponding project

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    logger.info("Syncing Storage objects for project %s.", project_id)
    storage_res = get_gcp_buckets(storage, project_id)
    raw_buckets = storage_res.get("items", [])  # for labels
    buckets, bucket_labels = transform_gcp_buckets_and_labels(storage_res)
    load_gcp_buckets(neo4j_session, buckets, project_id, gcp_update_tag)
    load_gcp_bucket_labels(neo4j_session, bucket_labels, project_id, gcp_update_tag)
    sync_labels(
        neo4j_session,
        raw_buckets,
        "gcp_bucket",
        project_id,
        gcp_update_tag,
        common_job_parameters,
    )
    cleanup_gcp_buckets(neo4j_session, common_job_parameters)
