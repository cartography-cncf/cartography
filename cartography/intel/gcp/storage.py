import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.intel.gcp import compute
from cartography.util import run_cleanup_job
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
        req = storage.buckets().list(project=project_id)
        res = req.execute()
        return res
    except HttpError as e:
        reason = compute._get_error_reason(e)
        if reason == "invalid":
            logger.warning(
                (
                    "The project %s is invalid - returned a 400 invalid error."
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return {}
        elif reason == "forbidden":
            logger.warning(
                (
                    "You do not have storage.bucket.list access to the project %s. "
                    "Full details: %s"
                ),
                project_id,
                e,
            )
            return {}
        else:
            raise


@timeit
def transform_gcp_buckets(bucket_res: Dict) -> List[Dict]:
    """
    Transform the GCP Storage Bucket response object for Neo4j ingestion

    :type bucket_res: The GCP storage resource object (https://cloud.google.com/storage/docs/json_api/v1/buckets)
    :param bucket_res: The return data

    :rtype: list
    :return: List of buckets ready for ingestion to Neo4j
    """

    bucket_list = []
    for b in bucket_res.get("items", []):
        bucket = {}
        bucket["etag"] = b.get("etag")
        bucket["iam_config_bucket_policy_only"] = (
            b.get("iamConfiguration", {})
            .get("bucketPolicyOnly", {})
            .get("enabled", None)
        )
        bucket["id"] = b["id"]
        bucket["labels"] = [(key, val) for (key, val) in b.get("labels", {}).items()]
        bucket["owner_entity"] = b.get("owner", {}).get("entity")
        bucket["owner_entity_id"] = b.get("owner", {}).get("entityId")
        bucket["kind"] = b.get("kind")
        bucket["location"] = b.get("location")
        bucket["location_type"] = b.get("locationType")
        bucket["meta_generation"] = b.get("metageneration", None)
        bucket["project_number"] = b["projectNumber"]
        bucket["self_link"] = b.get("selfLink")
        bucket["storage_class"] = b.get("storageClass")
        bucket["time_created"] = b.get("timeCreated")
        bucket["updated"] = b.get("updated")
        bucket["versioning_enabled"] = b.get("versioning", {}).get("enabled", None)
        bucket["default_event_based_hold"] = b.get("defaultEventBasedHold", None)
        bucket["retention_period"] = b.get("retentionPolicy", {}).get(
            "retentionPeriod",
            None,
        )
        bucket["default_kms_key_name"] = b.get("encryption", {}).get(
            "defaultKmsKeyName",
        )
        bucket["log_bucket"] = b.get("logging", {}).get("logBucket")
        bucket["requester_pays"] = b.get("billing", {}).get("requesterPays", None)
        bucket_list.append(bucket)
    return bucket_list


@timeit
def load_gcp_buckets(
    neo4j_session: neo4j.Session,
    buckets: List[Dict],
    gcp_update_tag: int,
) -> None:
    """
    Ingest GCP Storage Buckets to Neo4j

    :type neo4j_session: Neo4j session object
    :param neo4j session: The Neo4j session object

    :type buckets: list
    :param buckets: List of GCP Storage Buckets to injest

    :type gcp_update_tag: timestamp
    :param gcp_update_tag: The timestamp value to set our new Neo4j nodes with

    :rtype: NoneType
    :return: Nothing
    """

    query = """
    MERGE(p:GCPProject{projectnumber:$ProjectNumber})
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $gcp_update_tag

    MERGE(bucket:GCPBucket{id:$BucketId})
    ON CREATE SET bucket.firstseen = timestamp(),
    bucket.bucket_id = $BucketId
    SET bucket.self_link = $SelfLink,
    bucket.project_number = $ProjectNumber,
    bucket.kind = $Kind,
    bucket.location = $Location,
    bucket.location_type = $LocationType,
    bucket.meta_generation = $MetaGeneration,
    bucket.storage_class = $StorageClass,
    bucket.time_created = $TimeCreated,
    bucket.retention_period = $RetentionPeriod,
    bucket.iam_config_bucket_policy_only = $IamConfigBucketPolicyOnly,
    bucket.owner_entity = $OwnerEntity,
    bucket.owner_entity_id = $OwnerEntityId,
    bucket.lastupdated = $gcp_update_tag,
    bucket.versioning_enabled = $VersioningEnabled,
    bucket.log_bucket = $LogBucket,
    bucket.requester_pays = $RequesterPays,
    bucket.default_kms_key_name = $DefaultKmsKeyName

    MERGE (p)-[r:RESOURCE]->(bucket)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    for bucket in buckets:
        neo4j_session.run(
            query,
            ProjectNumber=bucket["project_number"],
            BucketId=bucket["id"],
            SelfLink=bucket["self_link"],
            Kind=bucket["kind"],
            Location=bucket["location"],
            LocationType=bucket["location_type"],
            MetaGeneration=bucket["meta_generation"],
            StorageClass=bucket["storage_class"],
            TimeCreated=bucket["time_created"],
            RetentionPeriod=bucket["retention_period"],
            IamConfigBucketPolicyOnly=bucket["iam_config_bucket_policy_only"],
            OwnerEntity=bucket["owner_entity"],
            OwnerEntityId=bucket["owner_entity_id"],
            VersioningEnabled=bucket["versioning_enabled"],
            LogBucket=bucket["log_bucket"],
            RequesterPays=bucket["requester_pays"],
            DefaultKmsKeyName=bucket["default_kms_key_name"],
            gcp_update_tag=gcp_update_tag,
        )
        _attach_gcp_bucket_labels(neo4j_session, bucket, gcp_update_tag)


@timeit
def _attach_gcp_bucket_labels(
    neo4j_session: neo4j.Session,
    bucket: Resource,
    gcp_update_tag: int,
) -> None:
    """
    Attach GCP bucket labels to the bucket.
    :param neo4j_session: The neo4j session
    :param bucket: The GCP bucket object
    :param gcp_update_tag: The update tag for this sync
    :return: Nothing
    """
    query = """
    MERGE (l:Label:GCPBucketLabel{id: $BucketLabelId})
    ON CREATE SET l.firstseen = timestamp(),
    l.key = $Key
    SET l.value = $Value,
    l.lastupdated = $gcp_update_tag
    WITH l
    MATCH (bucket:GCPBucket{id:$BucketId})
    MERGE (l)<-[r:LABELED]-(bucket)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $gcp_update_tag
    """
    for key, val in bucket.get("labels", []):
        neo4j_session.run(
            query,
            BucketLabelId=f"GCPBucket_{key}",
            Key=key,
            Value=val,
            BucketId=bucket["id"],
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def cleanup_gcp_buckets(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Delete out-of-date GCP Storage Bucket nodes and relationships

    :type neo4j_session: The Neo4j session object
    :param neo4j_session: The Neo4j session

    :type common_job_parameters: dict
    :param common_job_parameters: Dictionary of other job parameters to pass to Neo4j

    :rtype: NoneType
    :return: Nothing
    """
    run_cleanup_job(
        "gcp_storage_bucket_cleanup.json",
        neo4j_session,
        common_job_parameters,
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
    bucket_list = transform_gcp_buckets(storage_res)
    load_gcp_buckets(neo4j_session, bucket_list, gcp_update_tag)
    # TODO scope the cleanup to the current project - https://github.com/cartography-cncf/cartography/issues/381
    cleanup_gcp_buckets(neo4j_session, common_job_parameters)
