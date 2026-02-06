import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import neo4j
from google.api_core import exceptions
from google.cloud import storage

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.storage.bucket import GCPBucketLabelSchema
from cartography.models.gcp.storage.bucket import GCPBucketSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_buckets(
    project_id: str, credentials: Any = None
) -> Dict[str, Any]:
    """
    Returns a list of storage buckets within some given project using google-cloud-storage SDK.

    The google-cloud-storage SDK provides automatic retry logic for transient errors (429, 5xx)
    with exponential backoff, better type safety, and cleaner API interface.

    :type project_id: str
    :param project_id: The Google Project Id that you are retrieving buckets from

    :type credentials: google.auth.credentials.Credentials
    :param credentials: The GCP credentials object

    :rtype: Dict[str, Any]
    :return: Dictionary with 'items' key containing list of bucket dictionaries
    """
    try:
        # Initialize the Storage client with automatic retry handling
        # The SDK handles pagination and retries automatically
        client = storage.Client(project=project_id, credentials=credentials)

        buckets_data = []
        # list_buckets() returns an iterator that handles pagination automatically
        for bucket in client.list_buckets():
            # Convert Bucket object to dictionary format for compatibility with existing schema
            bucket_dict = {
                "id": bucket.name,
                "kind": "storage#bucket",
                "selfLink": f"https://www.googleapis.com/storage/v1/b/{bucket.name}",
                "projectNumber": bucket.project_number,
                "name": bucket.name,
                "timeCreated": bucket.time_created.isoformat() if bucket.time_created else None,
                "updated": bucket.updated.isoformat() if bucket.updated else None,
                "metageneration": bucket.metageneration,
                "location": bucket.location,
                "locationType": bucket.location_type,
                "storageClass": bucket.storage_class,
                "labels": dict(bucket.labels) if bucket.labels else {},
            }

            # Add IAM configuration if available
            if bucket.iam_configuration:
                bucket_dict["iamConfiguration"] = {
                    "bucketPolicyOnly": {
                        "enabled": bucket.iam_configuration.bucket_policy_only_enabled,
                    }
                }

            # Add owner information if available
            if hasattr(bucket, "owner") and bucket.owner:
                bucket_dict["owner"] = bucket.owner

            # Add versioning configuration
            if bucket.versioning_enabled is not None:
                bucket_dict["versioning"] = {"enabled": bucket.versioning_enabled}

            # Add retention policy if configured
            if bucket.retention_policy_effective_time:
                bucket_dict["retentionPolicy"] = {
                    "retentionPeriod": bucket.retention_period,
                    "effectiveTime": bucket.retention_policy_effective_time.isoformat(),
                }

            # Add encryption configuration if available
            if bucket.default_kms_key_name:
                bucket_dict["encryption"] = {
                    "defaultKmsKeyName": bucket.default_kms_key_name,
                }

            # Add logging configuration if available
            if hasattr(bucket, "log_bucket") and bucket.log_bucket:
                bucket_dict["logging"] = {"logBucket": bucket.log_bucket}

            # Add billing configuration
            if bucket.requester_pays is not None:
                bucket_dict["billing"] = {"requesterPays": bucket.requester_pays}

            buckets_data.append(bucket_dict)

        return {"items": buckets_data}

    except exceptions.Forbidden as e:
        logger.warning(
            "You do not have storage.buckets.list permission for project %s. "
            "Error: %s",
            project_id,
            e,
        )
        return {}
    except exceptions.InvalidArgument as e:
        logger.warning(
            "The project %s is invalid - returned an invalid argument error. "
            "Error: %s",
            project_id,
            e,
        )
        return {}
    except Exception as e:
        logger.error(
            "Unexpected error retrieving buckets for project %s: %s",
            project_id,
            e,
            exc_info=True,
        )
        raise  # Re-raise to prevent data loss via cleanup


@timeit
def transform_gcp_buckets_and_labels(bucket_res: Dict) -> Tuple[List[Dict], List[Dict]]:
    """
    Transform the GCP Storage Bucket response object for Neo4j ingestion.

    :param bucket_res: The raw GCP bucket response.
    :return: A tuple of (buckets, bucket_labels) ready for ingestion to Neo4j.
    """

    buckets: List[Dict] = []
    labels: List[Dict] = []
    for b in bucket_res.get("items", []):
        bucket = {
            "iam_config_bucket_policy_only": (
                b.get("iamConfiguration", {}).get("bucketPolicyOnly", {}).get("enabled")
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
    credentials: Any,
    project_id: str,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP Storage buckets using the google-cloud-storage SDK, ingest to Neo4j, and clean up old data.

    The google-cloud-storage SDK provides automatic retry logic for transient errors,
    eliminating the need for manual retry handling.

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session

    :type credentials: google.auth.credentials.Credentials
    :param credentials: The GCP credentials object

    :type project_id: str
    :param project_id: The project ID of the corresponding project

    :type gcp_update_tag: int
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    logger.info("Syncing Storage buckets for project %s.", project_id)
    storage_res = get_gcp_buckets(project_id, credentials)
    buckets, bucket_labels = transform_gcp_buckets_and_labels(storage_res)
    load_gcp_buckets(neo4j_session, buckets, project_id, gcp_update_tag)
    load_gcp_bucket_labels(neo4j_session, bucket_labels, project_id, gcp_update_tag)
    cleanup_gcp_buckets(neo4j_session, common_job_parameters)
