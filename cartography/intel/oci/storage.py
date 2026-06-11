# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Storage API-centric functions
# Object Storage: https://docs.oracle.com/en-us/iaas/Content/Object/Concepts/objectstorageoverview.htm
# File Storage: https://docs.oracle.com/en-us/iaas/Content/File/Concepts/filestorageoverview.htm
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci
import oci.file_storage
import oci.identity
import oci.object_storage

from . import utils
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


# ============================================================
# Object Storage Buckets
# ============================================================

def get_namespace(
    object_storage: oci.object_storage.ObjectStorageClient,
) -> str:
    """
    Get the Object Storage namespace for the tenancy.
    """
    try:
        return object_storage.get_namespace().data
    except oci.exceptions.ServiceError as e:
        logger.warning("Could not retrieve Object Storage namespace: %s", e.message)
        return ""


def get_bucket_list_data(
    object_storage: oci.object_storage.ObjectStorageClient,
    namespace: str,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all buckets in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/latest/Bucket/ListBuckets
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            object_storage.list_buckets,
            namespace_name=namespace,
            compartment_id=compartment_id,
        )
        return {'Buckets': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve buckets for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Buckets': []}


def get_bucket_details(
    object_storage: oci.object_storage.ObjectStorageClient,
    namespace: str,
    bucket_name: str,
) -> Dict[str, Any]:
    """
    Get full details for a single bucket (includes versioning, public access,
    kms_key_id, retention rules, etc.).
    See https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/latest/Bucket/GetBucket
    """
    try:
        response = object_storage.get_bucket(
            namespace_name=namespace,
            bucket_name=bucket_name,
            fields=["approximateCount", "approximateSize"],
        )
        return utils.oci_single_object_to_json(response.data)
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve bucket details for '%s': %s",
            bucket_name, e.message,
        )
        return {}


def get_bucket_retention_rules(
    object_storage: oci.object_storage.ObjectStorageClient,
    namespace: str,
    bucket_name: str,
) -> List[Dict[str, Any]]:
    """
    Get retention rules for a bucket.
    """
    try:
        response = object_storage.list_retention_rules(
            namespace_name=namespace,
            bucket_name=bucket_name,
        )
        return utils.oci_object_to_json(response.data.items)
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve retention rules for bucket '%s': %s",
            bucket_name, e.message,
        )
        return []
    except AttributeError:
        # response.data may not have .items in older SDK versions
        return []


def load_buckets(
    neo4j_session: neo4j.Session,
    buckets: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Object Storage Bucket data into Neo4j.
    """
    ingest_bucket = """
    MERGE (b:OCIObjectStorageBucket{name: $NAME, namespace: $NAMESPACE})
    ON CREATE SET b.firstseen = timestamp(),
    b.createdate = $TIME_CREATED
    SET b.display_name = $NAME,
    b.compartment_id = $COMPARTMENT_ID,
    b.namespace = $NAMESPACE,
    b.public_access_type = $PUBLIC_ACCESS_TYPE,
    b.storage_tier = $STORAGE_TIER,
    b.versioning = $VERSIONING,
    b.kms_key_id = $KMS_KEY_ID,
    b.is_read_only = $IS_READ_ONLY,
    b.object_lifecycle_policy_etag = $OBJECT_LIFECYCLE_POLICY_ETAG,
    b.approximate_count = $APPROXIMATE_COUNT,
    b.approximate_size = $APPROXIMATE_SIZE,
    b.has_retention_rules = $HAS_RETENTION_RULES,
    b.object_events_enabled = $OBJECT_EVENTS_ENABLED,
    b.region = $REGION,
    b.lastupdated = $oci_update_tag
    WITH b
    MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(b)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for bucket in buckets:
        neo4j_session.run(
            ingest_bucket,
            NAME=bucket.get("name", ""),
            NAMESPACE=bucket.get("namespace", ""),
            COMPARTMENT_ID=bucket.get("compartment-id", compartment_id),
            PUBLIC_ACCESS_TYPE=bucket.get("public-access-type", "NoPublicAccess"),
            STORAGE_TIER=bucket.get("storage-tier", ""),
            VERSIONING=bucket.get("versioning", "Disabled"),
            KMS_KEY_ID=bucket.get("kms-key-id", ""),
            IS_READ_ONLY=bucket.get("is-read-only", False),
            OBJECT_LIFECYCLE_POLICY_ETAG=bucket.get(
                "object-lifecycle-policy-etag", "",
            ),
            APPROXIMATE_COUNT=bucket.get("approximate-count"),
            APPROXIMATE_SIZE=bucket.get("approximate-size"),
            HAS_RETENTION_RULES=bucket.get("_has_retention_rules", False),
            OBJECT_EVENTS_ENABLED=bucket.get("object-events-enabled", False),
            REGION=region,
            TIME_CREATED=str(bucket.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_buckets(
    neo4j_session: neo4j.Session,
    object_storage: oci.object_storage.ObjectStorageClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all Object Storage buckets across compartments.
    For each bucket, fetch full details (versioning, kms, public access) and
    retention rules.
    """
    logger.debug(
        "Syncing OCI Object Storage buckets for tenancy '%s', region '%s'.",
        tenancy_id, region,
    )
    namespace = get_namespace(object_storage)
    if not namespace:
        return

    for compartment in compartments:
        data = get_bucket_list_data(object_storage, namespace, compartment["ocid"])
        enriched_buckets: List[Dict[str, Any]] = []
        for bucket_summary in data["Buckets"]:
            bucket_name = bucket_summary.get("name", "")
            if not bucket_name:
                continue
            details = get_bucket_details(object_storage, namespace, bucket_name)
            if not details:
                continue
            # Determine if retention rules exist
            retention_rules = get_bucket_retention_rules(
                object_storage, namespace, bucket_name,
            )
            details["_has_retention_rules"] = len(retention_rules) > 0
            enriched_buckets.append(details)
        if enriched_buckets:
            load_buckets(
                neo4j_session, enriched_buckets, tenancy_id,
                compartment["ocid"], region, oci_update_tag,
            )


# ============================================================
# File Storage - File Systems
# ============================================================

def get_file_system_list_data(
    file_storage: oci.file_storage.FileStorageClient,
    compartment_id: str,
    availability_domain: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all file systems in a compartment for a given availability domain.
    See https://docs.oracle.com/en-us/iaas/api/#/en/filestorage/latest/FileSystemSummary/ListFileSystems
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            file_storage.list_file_systems,
            compartment_id=compartment_id,
            availability_domain=availability_domain,
        )
        return {'FileSystems': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve file systems for compartment '%s', AD '%s': %s",
            compartment_id, availability_domain, e.message,
        )
        return {'FileSystems': []}


def load_file_systems(
    neo4j_session: neo4j.Session,
    file_systems: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI File Storage file system data into Neo4j.
    """
    ingest_fs = """
    MERGE (fs:OCIFileSystem{ocid: $OCID})
    ON CREATE SET fs.firstseen = timestamp(),
    fs.createdate = $TIME_CREATED
    SET fs.display_name = $DISPLAY_NAME,
    fs.compartment_id = $COMPARTMENT_ID,
    fs.availability_domain = $AVAILABILITY_DOMAIN,
    fs.lifecycle_state = $LIFECYCLE_STATE,
    fs.kms_key_id = $KMS_KEY_ID,
    fs.metered_bytes = $METERED_BYTES,
    fs.region = $REGION,
    fs.lastupdated = $oci_update_tag
    WITH fs
    MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(fs)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for fs in file_systems:
        neo4j_session.run(
            ingest_fs,
            OCID=fs.get("id"),
            DISPLAY_NAME=fs.get("display-name"),
            COMPARTMENT_ID=fs.get("compartment-id", compartment_id),
            AVAILABILITY_DOMAIN=fs.get("availability-domain", ""),
            LIFECYCLE_STATE=fs.get("lifecycle-state"),
            KMS_KEY_ID=fs.get("kms-key-id", ""),
            METERED_BYTES=fs.get("metered-bytes"),
            REGION=region,
            TIME_CREATED=str(fs.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_file_systems(
    neo4j_session: neo4j.Session,
    file_storage: oci.file_storage.FileStorageClient,
    identity: oci.identity.identity_client.IdentityClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all File Storage file systems across compartments and availability domains.
    """
    logger.debug(
        "Syncing OCI File Storage file systems for tenancy '%s', region '%s'.",
        tenancy_id, region,
    )
    # Get availability domains (file systems are scoped per AD)
    availability_domains: List[str] = []
    for compartment in compartments:
        try:
            response = identity.list_availability_domains(
                compartment_id=compartment["ocid"],
            )
            availability_domains.extend([ad.name for ad in response.data])
        except oci.exceptions.ServiceError as e:
            logger.warning(
                "Could not retrieve ADs for compartment '%s': %s",
                compartment["ocid"], e.message,
            )
    availability_domains = list(dict.fromkeys(availability_domains))

    for compartment in compartments:
        for ad in availability_domains:
            data = get_file_system_list_data(
                file_storage, compartment["ocid"], ad,
            )
            if data["FileSystems"]:
                load_file_systems(
                    neo4j_session, data["FileSystems"], tenancy_id,
                    compartment["ocid"], region, oci_update_tag,
                )


# ============================================================
# Top-level sync function
# ============================================================

def sync(
    neo4j_session: neo4j.Session,
    storage: oci.object_storage.ObjectStorageClient,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: List[str] = None,
) -> None:
    """
    Sync OCI Storage resources (Object Storage buckets and File Storage file systems)
    for the compartment specified in common_job_parameters.
    """
    compartment_ocid = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    logger.info("Syncing OCI Storage for compartment '%s'.", compartment_ocid)

    compartments = [
        {"ocid": compartment_ocid, "name": "target", "compartmentid": tenancy_id},
    ]

    if not regions:
        regions = [storage.base_client.region or ""]

    # Create additional clients from the storage client's config/signer.
    file_storage = oci.file_storage.FileStorageClient(
        config=storage.base_client.config,
        signer=getattr(storage.base_client, "signer", None),
    )
    identity = oci.identity.IdentityClient(
        config=storage.base_client.config,
        signer=getattr(storage.base_client, "signer", None),
    )

    for region in regions:
        logger.info(
            "Syncing OCI Storage in region '%s' for compartment '%s'.",
            region, compartment_ocid,
        )
        storage.base_client.set_region(region)
        file_storage.base_client.set_region(region)
        identity.base_client.set_region(region)

        # Sync Object Storage buckets
        sync_buckets(
            neo4j_session, storage, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

        # Sync File Storage file systems
        sync_file_systems(
            neo4j_session, file_storage, identity, compartments,
            tenancy_id, region, oci_update_tag, common_job_parameters,
        )

    # Cleanup stale storage nodes
    run_cleanup_job(
        'oci_import_storage_cleanup.json', neo4j_session, common_job_parameters,
    )
