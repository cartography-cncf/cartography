import json
import logging
from typing import Any, Dict, List

import neo4j
from googleapiclient.discovery import HttpError, Resource

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.storage import GCPBucketLabelSchema, GCPStorageBucketSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_buckets(storage: Resource, project_id: str) -> List[Dict[str, Any]]:
    """
    Returns a list of storage bucket objects within a given project.
    This function handles pagination and will return an empty list if the API is not enabled
    or if the permissions are missing.
    """
    logger.info(f"Collecting Storage Buckets for project: {project_id}")
    collected_buckets: List[Dict[str, Any]] = []
    try:
        request = storage.buckets().list(project=project_id)
        while request is not None:
            response = request.execute()
            if 'items' in response:
                collected_buckets.extend(response['items'])
            request = storage.buckets().list_next(
                previous_request=request, previous_response=response,
            )
        return collected_buckets
    except HttpError as e:
        error_json = json.loads(e.content.decode("utf-8"))
        err = error_json.get("error", {})
        if (
            err.get("status", "") == "PERMISSION_DENIED"
            or (err.get("message") and "API has not been used" in err.get("message"))
        ):
            logger.warning(
                (
                    "Could not retrieve Storage Buckets on project %s due to permissions issues or API not enabled. "
                    "Code: %s, Message: %s"
                ),
                project_id,
                err.get("code"),
                err.get("message"),
            )
            return []
        elif e.resp.status in [404]:
            logger.warning(
                (
                    "Project %s returned a 404 not found error. This may mean the project has no buckets. "
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return []
        else:
            raise


@timeit
def transform_gcp_buckets(buckets_response: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms the GCP Storage Bucket response list for Neo4j ingestion by flattening
    and preparing label data.
    """
    bucket_list: List[Dict[str, Any]] = []
    for b in buckets_response:
        transformed_labels: List[Dict[str, Any]] = []
        for key, val in b.get("labels", {}).items():
            transformed_labels.append({
                "id": f"{b['id']}_{key}",
                "key": key,
                "value": val,
                "bucket_id": b["id"],
                "project_number": b["projectNumber"],
            })

        transformed_bucket = {
            "id": b["id"],
            "project_number": b["projectNumber"],
            "etag": b.get("etag"),
            "owner_entity": b.get("owner", {}).get("entity"),
            "owner_entity_id": b.get("owner", {}).get("entityId"),
            "kind": b.get("kind"),
            "location": b.get("location"),
            "location_type": b.get("locationType"),
            "meta_generation": b.get("metageneration"),
            "self_link": b.get("selfLink"),
            "storage_class": b.get("storageClass"),
            "time_created": b.get("timeCreated"),
            "updated": b.get("updated"),
            "versioning_enabled": b.get("versioning", {}).get("enabled"),
            "default_event_based_hold": b.get("defaultEventBasedHold"),
            "retention_period": b.get("retentionPolicy", {}).get("retentionPeriod"),
            "default_kms_key_name": b.get("encryption", {}).get("defaultKmsKeyName"),
            "log_bucket": b.get("logging", {}).get("logBucket"),
            "requester_pays": b.get("billing", {}).get("requesterPays"),
            "iam_config_bucket_policy_only": b.get("iamConfiguration", {}).get("bucketPolicyOnly", {}).get("enabled"),
            "labels": transformed_labels,
            "label_ids": [label['id'] for label in transformed_labels],
        }

        bucket_list.append(transformed_bucket)
    return bucket_list



@timeit
def load_gcp_buckets(
    neo4j_session: neo4j.Session,
    buckets: List[Dict[str, Any]],
    project_id: str,
    gcp_update_tag: int,
) -> None:
    """
    Ingests GCP Storage Buckets and their associated Labels to Neo4j using the declarative loader.
    """
    # FIRST, load all the GCPBucketLabel nodes so they exist in the graph.
    all_labels: List[Dict[str, Any]] = []
    for bucket in buckets:
        all_labels.extend(bucket.get("labels", []))

    if all_labels:
        logger.info(f"Loading {len(all_labels)} GCP Storage Bucket Labels for project {project_id}.")
        load(
            neo4j_session,
            GCPBucketLabelSchema(),
            all_labels,
            lastupdated=gcp_update_tag,
            project_number=project_id,
        )

    # SECOND, load the GCPStorageBucket nodes.
    logger.info(f"Loading {len(buckets)} GCP Storage Buckets for project {project_id}.")
    load(
        neo4j_session,
        GCPStorageBucketSchema(),
        buckets,
        lastupdated=gcp_update_tag,
        project_number=project_id,
    )

@timeit
def cleanup_gcp_buckets(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Deletes out-of-date GCP Storage Bucket and GCPBucketLabel nodes using the modern GraphJob.
    """
    logger.debug("Running GCP Storage Bucket cleanup job.")
    GraphJob.from_node_schema(GCPStorageBucketSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(GCPBucketLabelSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_gcp_buckets(
    neo4j_session: neo4j.Session,
    storage: Resource,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    The main orchestration function to get, transform, load, and clean up GCP Storage Buckets.
    """
    logger.info(f"Syncing GCP Storage Buckets for project {project_id}.")
    buckets_response = get_gcp_buckets(storage, project_id)

    if not buckets_response:
        logger.info(f"No Storage Buckets found for project {project_id}, skipping transform and load.")
    else:
        bucket_list = transform_gcp_buckets(buckets_response)
        load_gcp_buckets(neo4j_session, bucket_list, project_id, gcp_update_tag)

    cleanup_job_params = common_job_parameters.copy()
    cleanup_job_params["project_number"] = project_id
    cleanup_gcp_buckets(neo4j_session, cleanup_job_params)