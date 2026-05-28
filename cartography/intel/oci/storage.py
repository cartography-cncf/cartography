# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Storage API-centric functions.
#
# Covers:
#   - Object Storage (Buckets)         https://docs.oracle.com/en-us/iaas/Content/Object/Concepts/objectstorageoverview.htm
#   - Block Volumes                    https://docs.oracle.com/en-us/iaas/Content/Block/Concepts/overview.htm
#   - Boot Volumes                     https://docs.oracle.com/en-us/iaas/Content/Block/Concepts/bootvolumes.htm
#   - Volume Backups (Block + Boot)    https://docs.oracle.com/en-us/iaas/Content/Block/Concepts/blockvolumebackups.htm
#   - File Storage (File Systems)      https://docs.oracle.com/en-us/iaas/Content/File/Concepts/filestorageoverview.htm
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
import oci

from . import utils
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


class OCIStorageClients:
    """
    Lightweight container that bundles the three OCI SDK clients required to
    cover the full storage surface area. The OCI sync orchestrator resolves a
    single client per resource family via ``getattr(resources, sync_name)``;
    storage spans three SDK clients, so we wrap them here behind one attribute.
    """

    def __init__(
        self,
        object_storage: oci.object_storage.ObjectStorageClient,
        blockstorage: oci.core.BlockstorageClient,
        file_storage: oci.file_storage.FileStorageClient,
    ) -> None:
        self.object_storage = object_storage
        self.blockstorage = blockstorage
        self.file_storage = file_storage

    def set_region(self, region: str) -> None:
        """Pin every underlying SDK client to the given OCI region."""
        if not region:
            return
        self.object_storage.base_client.set_region(region)
        self.blockstorage.base_client.set_region(region)
        self.file_storage.base_client.set_region(region)


# ---------------------------------------------------------------------------
# Object Storage: Buckets
# ---------------------------------------------------------------------------

def get_object_storage_namespace(
    object_storage: oci.object_storage.ObjectStorageClient,
    compartment_id: str,
) -> str:
    """
    Resolve the Object Storage namespace for the tenancy. Required for every
    bucket-level call. See:
    https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/latest/Namespace/GetNamespace
    """
    try:
        response = object_storage.get_namespace(compartment_id=compartment_id)
        return response.data or ""
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve Object Storage namespace for compartment '%s': %s",
            compartment_id, e.message,
        )
        return ""


def get_bucket_list_data(
    object_storage: oci.object_storage.ObjectStorageClient,
    namespace: str,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all Object Storage buckets in a compartment. Note: ``ListBuckets`` only
    returns summaries; bucket-level security posture (public access type,
    versioning, KMS key, replication) requires ``GetBucket``.
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
            "Could not retrieve Object Storage buckets for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Buckets': []}


def get_bucket_details(
    object_storage: oci.object_storage.ObjectStorageClient,
    namespace: str,
    bucket_name: str,
) -> Dict[str, Any]:
    """
    Fetch the full Bucket object including security-relevant fields that are
    not returned by ListBuckets: ``public-access-type``, ``versioning``,
    ``kms-key-id``, ``replication-enabled``, ``object-events-enabled``,
    plus approximate object count and size.
    """
    try:
        response = object_storage.get_bucket(
            namespace_name=namespace,
            bucket_name=bucket_name,
            fields=["approximateCount", "approximateSize"],
        )
        rows = utils.oci_object_to_json(f"[{response.data}]")
        return rows[0] if rows else {}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve bucket details for '%s/%s': %s",
            namespace, bucket_name, e.message,
        )
        return {}


def transform_buckets(
    bucket_summaries: List[Dict[str, Any]],
    bucket_details_by_name: Dict[str, Dict[str, Any]],
    namespace: str,
    region: str,
) -> List[Dict[str, Any]]:
    """
    Merge the per-bucket detail payload back onto each summary row and shape
    the dicts to the keys our load_buckets Cypher expects.
    """
    transformed: List[Dict[str, Any]] = []
    for summary in bucket_summaries:
        name = summary.get("name")
        if not name:
            continue
        details = bucket_details_by_name.get(name, {})
        merged = {**summary, **details}
        transformed.append({
            "ocid": merged.get("id") or f"oci.bucket.{namespace}.{name}",
            "name": name,
            "namespace": namespace,
            "compartment_id": merged.get("compartment-id"),
            "created_by": merged.get("created-by"),
            "etag": merged.get("etag"),
            "public_access_type": merged.get("public-access-type") or "NoPublicAccess",
            "storage_tier": merged.get("storage-tier") or "Standard",
            "object_events_enabled": bool(merged.get("object-events-enabled", False)),
            "replication_enabled": bool(merged.get("replication-enabled", False)),
            "is_read_only": bool(merged.get("is-read-only", False)),
            "versioning": merged.get("versioning") or "Disabled",
            "auto_tiering": merged.get("auto-tiering") or "Disabled",
            "kms_key_id": merged.get("kms-key-id"),
            "object_lifecycle_policy_etag": merged.get("object-lifecycle-policy-etag"),
            "approximate_count": merged.get("approximate-count"),
            "approximate_size": merged.get("approximate-size"),
            "time_created": str(merged.get("time-created", "")),
            "region": region,
        })
    return transformed


def load_buckets(
    neo4j_session: neo4j.Session,
    buckets: List[Dict[str, Any]],
    compartment_id: str,
    oci_update_tag: int,
) -> None:
    """
    Batch-ingest OCIStorageBucket nodes and attach them to their owning
    OCICompartment via the standard RESOURCE relationship.
    """
    ingest_buckets = """
    UNWIND $buckets AS bucket
        MERGE (b:OCIStorageBucket{ocid: bucket.ocid})
        ON CREATE SET b.firstseen = timestamp(),
                      b.createdate = bucket.time_created
        SET b.name = bucket.name,
            b.namespace = bucket.namespace,
            b.compartment_id = bucket.compartment_id,
            b.created_by = bucket.created_by,
            b.etag = bucket.etag,
            b.public_access_type = bucket.public_access_type,
            b.is_public = (bucket.public_access_type <> 'NoPublicAccess'),
            b.storage_tier = bucket.storage_tier,
            b.object_events_enabled = bucket.object_events_enabled,
            b.replication_enabled = bucket.replication_enabled,
            b.is_read_only = bucket.is_read_only,
            b.versioning = bucket.versioning,
            b.auto_tiering = bucket.auto_tiering,
            b.kms_key_id = bucket.kms_key_id,
            b.is_encrypted_with_cmk = (bucket.kms_key_id IS NOT NULL),
            b.object_lifecycle_policy_etag = bucket.object_lifecycle_policy_etag,
            b.approximate_count = bucket.approximate_count,
            b.approximate_size = bucket.approximate_size,
            b.region = bucket.region,
            b.lastupdated = $oci_update_tag
        WITH b
        MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
        MERGE (cc)-[r:RESOURCE]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(
        ingest_buckets,
        buckets=buckets,
        COMPARTMENT_ID=compartment_id,
        oci_update_tag=oci_update_tag,
    )


def sync_buckets(
    neo4j_session: neo4j.Session,
    object_storage: oci.object_storage.ObjectStorageClient,
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Fetch → transform → load Object Storage buckets for one compartment.
    """
    logger.debug(
        "Syncing OCI Object Storage buckets for compartment '%s', region '%s'.",
        compartment_id, region,
    )
    namespace = get_object_storage_namespace(object_storage, compartment_id)
    if not namespace:
        logger.warning(
            "Skipping Object Storage sync for compartment '%s' in region '%s': namespace unavailable.",
            compartment_id, region,
        )
        return

    summaries = get_bucket_list_data(object_storage, namespace, compartment_id)["Buckets"]
    if not summaries:
        return

    details_by_name: Dict[str, Dict[str, Any]] = {}
    for summary in summaries:
        name = summary.get("name")
        if not name:
            continue
        details = get_bucket_details(object_storage, namespace, name)
        if details:
            details_by_name[name] = details

    buckets = transform_buckets(summaries, details_by_name, namespace, region)
    if buckets:
        load_buckets(neo4j_session, buckets, compartment_id, oci_update_tag)


# ---------------------------------------------------------------------------
# Block Volumes
# ---------------------------------------------------------------------------

def get_block_volume_list_data(
    blockstorage: oci.core.BlockstorageClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List block volumes in a compartment. See:
    https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Volume/ListVolumes
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            blockstorage.list_volumes, compartment_id=compartment_id,
        )
        return {'Volumes': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve block volumes for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Volumes': []}


def transform_block_volumes(
    volumes: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for v in volumes:
        if not v.get("id"):
            continue
        source = v.get("source-details") or {}
        transformed.append({
            "ocid": v.get("id"),
            "display_name": v.get("display-name"),
            "compartment_id": v.get("compartment-id"),
            "availability_domain": v.get("availability-domain"),
            "lifecycle_state": v.get("lifecycle-state"),
            "size_in_gbs": v.get("size-in-gbs"),
            "size_in_mbs": v.get("size-in-mbs"),
            "vpus_per_gb": v.get("vpus-per-gb"),
            "is_hydrated": v.get("is-hydrated"),
            "kms_key_id": v.get("kms-key-id"),
            "volume_group_id": v.get("volume-group-id"),
            "source_type": source.get("type"),
            "source_id": source.get("id"),
            "auto_tuned_vpus_per_gb": v.get("auto-tuned-vpus-per-gb"),
            "is_auto_tune_enabled": v.get("is-auto-tune-enabled"),
            "time_created": str(v.get("time-created", "")),
            "region": region,
        })
    return transformed


def load_block_volumes(
    neo4j_session: neo4j.Session,
    volumes: List[Dict[str, Any]],
    compartment_id: str,
    oci_update_tag: int,
) -> None:
    """
    Batch-ingest OCIBlockVolume nodes scoped to a compartment, and link any
    attached compute instances (resolved from existing OCIVolumeAttachment
    nodes) via OCI_VOLUME_ATTACHMENT.
    """
    ingest_volumes = """
    UNWIND $volumes AS v
        MERGE (vol:OCIBlockVolume{ocid: v.ocid})
        ON CREATE SET vol.firstseen = timestamp(),
                      vol.createdate = v.time_created
        SET vol.display_name = v.display_name,
            vol.compartment_id = v.compartment_id,
            vol.availability_domain = v.availability_domain,
            vol.lifecycle_state = v.lifecycle_state,
            vol.size_in_gbs = v.size_in_gbs,
            vol.size_in_mbs = v.size_in_mbs,
            vol.vpus_per_gb = v.vpus_per_gb,
            vol.is_hydrated = v.is_hydrated,
            vol.kms_key_id = v.kms_key_id,
            vol.is_encrypted_with_cmk = (v.kms_key_id IS NOT NULL),
            vol.volume_group_id = v.volume_group_id,
            vol.source_type = v.source_type,
            vol.source_id = v.source_id,
            vol.auto_tuned_vpus_per_gb = v.auto_tuned_vpus_per_gb,
            vol.is_auto_tune_enabled = v.is_auto_tune_enabled,
            vol.region = v.region,
            vol.lastupdated = $oci_update_tag
        WITH vol
        MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
        MERGE (cc)-[r:RESOURCE]->(vol)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(
        ingest_volumes,
        volumes=volumes,
        COMPARTMENT_ID=compartment_id,
        oci_update_tag=oci_update_tag,
    )

    # Connect each block volume to every instance that currently has an
    # active attachment record for it. We rely on the OCIVolumeAttachment
    # nodes that compute.py already ingested.
    link_instances = """
    MATCH (vol:OCIBlockVolume)
    WHERE vol.lastupdated = $oci_update_tag
    MATCH (inst:OCIInstance)-[:OCI_VOLUME_ATTACHMENT]->(att:OCIVolumeAttachment)
    WHERE att.volume_id = vol.ocid
      AND att.lifecycle_state = 'ATTACHED'
    MERGE (inst)-[r:OCI_VOLUME_ATTACHMENT]->(vol)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(link_instances, oci_update_tag=oci_update_tag)


def sync_block_volumes(
    neo4j_session: neo4j.Session,
    blockstorage: oci.core.BlockstorageClient,
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    logger.debug(
        "Syncing OCI block volumes for compartment '%s', region '%s'.",
        compartment_id, region,
    )
    raw = get_block_volume_list_data(blockstorage, compartment_id)["Volumes"]
    volumes = transform_block_volumes(raw, region)
    if volumes:
        load_block_volumes(neo4j_session, volumes, compartment_id, oci_update_tag)


# ---------------------------------------------------------------------------
# Boot Volumes
# ---------------------------------------------------------------------------

def get_availability_domains(
    identity_client: Optional[oci.identity.identity_client.IdentityClient],
    compartment_id: str,
) -> List[str]:
    """
    Boot volumes and FSS list operations are scoped to a single availability
    domain. We therefore enumerate the compartment's availability domains via
    the IdentityClient. If no IdentityClient is provided (e.g. when storage is
    sync'd in isolation), we return an empty list and the caller should
    short-circuit gracefully.
    """
    if not identity_client:
        return []
    try:
        response = identity_client.list_availability_domains(compartment_id=compartment_id)
        return [ad.name for ad in (response.data or []) if getattr(ad, "name", None)]
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not list availability domains for compartment '%s': %s",
            compartment_id, e.message,
        )
        return []


def get_boot_volume_list_data(
    blockstorage: oci.core.BlockstorageClient,
    availability_domain: str,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List boot volumes in a compartment for a single availability domain. See:
    https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/BootVolume/ListBootVolumes
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            blockstorage.list_boot_volumes,
            availability_domain=availability_domain,
            compartment_id=compartment_id,
        )
        return {'BootVolumes': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve boot volumes for compartment '%s', AD '%s': %s",
            compartment_id, availability_domain, e.message,
        )
        return {'BootVolumes': []}


def transform_boot_volumes(
    boot_volumes: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for v in boot_volumes:
        if not v.get("id"):
            continue
        source = v.get("source-details") or {}
        transformed.append({
            "ocid": v.get("id"),
            "display_name": v.get("display-name"),
            "compartment_id": v.get("compartment-id"),
            "availability_domain": v.get("availability-domain"),
            "lifecycle_state": v.get("lifecycle-state"),
            "size_in_gbs": v.get("size-in-gbs"),
            "size_in_mbs": v.get("size-in-mbs"),
            "vpus_per_gb": v.get("vpus-per-gb"),
            "is_hydrated": v.get("is-hydrated"),
            "kms_key_id": v.get("kms-key-id"),
            "volume_group_id": v.get("volume-group-id"),
            "image_id": v.get("image-id"),
            "source_type": source.get("type"),
            "source_id": source.get("id"),
            "time_created": str(v.get("time-created", "")),
            "region": region,
        })
    return transformed


def load_boot_volumes(
    neo4j_session: neo4j.Session,
    boot_volumes: List[Dict[str, Any]],
    compartment_id: str,
    oci_update_tag: int,
) -> None:
    ingest_boot_volumes = """
    UNWIND $boot_volumes AS v
        MERGE (bv:OCIBootVolume{ocid: v.ocid})
        ON CREATE SET bv.firstseen = timestamp(),
                      bv.createdate = v.time_created
        SET bv.display_name = v.display_name,
            bv.compartment_id = v.compartment_id,
            bv.availability_domain = v.availability_domain,
            bv.lifecycle_state = v.lifecycle_state,
            bv.size_in_gbs = v.size_in_gbs,
            bv.size_in_mbs = v.size_in_mbs,
            bv.vpus_per_gb = v.vpus_per_gb,
            bv.is_hydrated = v.is_hydrated,
            bv.kms_key_id = v.kms_key_id,
            bv.is_encrypted_with_cmk = (v.kms_key_id IS NOT NULL),
            bv.volume_group_id = v.volume_group_id,
            bv.image_id = v.image_id,
            bv.source_type = v.source_type,
            bv.source_id = v.source_id,
            bv.region = v.region,
            bv.lastupdated = $oci_update_tag
        WITH bv
        MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
        MERGE (cc)-[r:RESOURCE]->(bv)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(
        ingest_boot_volumes,
        boot_volumes=boot_volumes,
        COMPARTMENT_ID=compartment_id,
        oci_update_tag=oci_update_tag,
    )

    # Link instances to boot volumes via existing OCIBootVolumeAttachment
    # nodes already produced by compute.py.
    link_instances = """
    MATCH (bv:OCIBootVolume)
    WHERE bv.lastupdated = $oci_update_tag
    MATCH (inst:OCIInstance)-[:OCI_BOOT_VOLUME_ATTACHMENT]->(att:OCIBootVolumeAttachment)
    WHERE att.boot_volume_id = bv.ocid
      AND att.lifecycle_state = 'ATTACHED'
    MERGE (inst)-[r:OCI_BOOT_VOLUME_ATTACHMENT]->(bv)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(link_instances, oci_update_tag=oci_update_tag)


def sync_boot_volumes(
    neo4j_session: neo4j.Session,
    blockstorage: oci.core.BlockstorageClient,
    tenancy_id: str,
    compartment_id: str,
    availability_domains: List[str],
    region: str,
    oci_update_tag: int,
) -> None:
    logger.debug(
        "Syncing OCI boot volumes for compartment '%s', region '%s'.",
        compartment_id, region,
    )
    aggregated: List[Dict[str, Any]] = []
    for ad in availability_domains:
        raw = get_boot_volume_list_data(blockstorage, ad, compartment_id)["BootVolumes"]
        aggregated.extend(raw)
    boot_volumes = transform_boot_volumes(aggregated, region)
    if boot_volumes:
        load_boot_volumes(neo4j_session, boot_volumes, compartment_id, oci_update_tag)


# ---------------------------------------------------------------------------
# Volume Backups (Block + Boot)
# ---------------------------------------------------------------------------

def get_volume_backup_list_data(
    blockstorage: oci.core.BlockstorageClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List backups for block volumes in a compartment. See:
    https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/VolumeBackup/ListVolumeBackups
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            blockstorage.list_volume_backups, compartment_id=compartment_id,
        )
        return {'VolumeBackups': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve block volume backups for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'VolumeBackups': []}


def get_boot_volume_backup_list_data(
    blockstorage: oci.core.BlockstorageClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List backups for boot volumes in a compartment. See:
    https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/BootVolumeBackup/ListBootVolumeBackups
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            blockstorage.list_boot_volume_backups, compartment_id=compartment_id,
        )
        return {'BootVolumeBackups': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve boot volume backups for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'BootVolumeBackups': []}


def transform_volume_backups(
    block_backups: List[Dict[str, Any]],
    boot_backups: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    """
    Normalize block-volume and boot-volume backups into a single shape so they
    can be loaded with one query and uniformly anchored to their parent volume
    via OCI_VOLUME_BACKUP. ``source_kind`` distinguishes the parent type.
    """
    out: List[Dict[str, Any]] = []
    for b in block_backups:
        if not b.get("id"):
            continue
        out.append({
            "ocid": b.get("id"),
            "display_name": b.get("display-name"),
            "compartment_id": b.get("compartment-id"),
            "lifecycle_state": b.get("lifecycle-state"),
            "type": b.get("type"),
            "source_type": b.get("source-type"),
            "source_kind": "BLOCK",
            "parent_volume_id": b.get("volume-id"),
            "size_in_gbs": b.get("size-in-gbs"),
            "size_in_mbs": b.get("size-in-mbs"),
            "unique_size_in_gbs": b.get("unique-size-in-gbs"),
            "unique_size_in_mbs": b.get("unique-size-in-mbs"),
            "kms_key_id": b.get("kms-key-id"),
            "expiration_time": str(b.get("expiration-time", "")),
            "time_created": str(b.get("time-created", "")),
            "time_request_received": str(b.get("time-request-received", "")),
            "region": region,
        })
    for b in boot_backups:
        if not b.get("id"):
            continue
        out.append({
            "ocid": b.get("id"),
            "display_name": b.get("display-name"),
            "compartment_id": b.get("compartment-id"),
            "lifecycle_state": b.get("lifecycle-state"),
            "type": b.get("type"),
            "source_type": b.get("source-type"),
            "source_kind": "BOOT",
            "parent_volume_id": b.get("boot-volume-id"),
            "size_in_gbs": b.get("size-in-gbs"),
            "size_in_mbs": None,
            "unique_size_in_gbs": b.get("unique-size-in-gbs"),
            "unique_size_in_mbs": None,
            "kms_key_id": b.get("kms-key-id"),
            "expiration_time": str(b.get("expiration-time", "")),
            "time_created": str(b.get("time-created", "")),
            "time_request_received": str(b.get("time-request-received", "")),
            "region": region,
        })
    return out


def load_volume_backups(
    neo4j_session: neo4j.Session,
    backups: List[Dict[str, Any]],
    oci_update_tag: int,
) -> None:
    """
    Ingest OCIVolumeBackup nodes and connect each to its parent (block or boot)
    volume via OCI_VOLUME_BACKUP. We split the linkage into two passes by
    source_kind so each MATCH lands on a single, well-typed parent label.
    """
    ingest_backups = """
    UNWIND $backups AS bk
        MERGE (b:OCIVolumeBackup{ocid: bk.ocid})
        ON CREATE SET b.firstseen = timestamp(),
                      b.createdate = bk.time_created
        SET b.display_name = bk.display_name,
            b.compartment_id = bk.compartment_id,
            b.lifecycle_state = bk.lifecycle_state,
            b.type = bk.type,
            b.source_type = bk.source_type,
            b.source_kind = bk.source_kind,
            b.parent_volume_id = bk.parent_volume_id,
            b.size_in_gbs = bk.size_in_gbs,
            b.size_in_mbs = bk.size_in_mbs,
            b.unique_size_in_gbs = bk.unique_size_in_gbs,
            b.unique_size_in_mbs = bk.unique_size_in_mbs,
            b.kms_key_id = bk.kms_key_id,
            b.is_encrypted_with_cmk = (bk.kms_key_id IS NOT NULL),
            b.expiration_time = bk.expiration_time,
            b.time_request_received = bk.time_request_received,
            b.region = bk.region,
            b.lastupdated = $oci_update_tag
    """
    neo4j_session.run(ingest_backups, backups=backups, oci_update_tag=oci_update_tag)

    link_block = """
    UNWIND $backups AS bk
        WITH bk WHERE bk.source_kind = 'BLOCK' AND bk.parent_volume_id IS NOT NULL
        MATCH (parent:OCIBlockVolume{ocid: bk.parent_volume_id})
        MATCH (b:OCIVolumeBackup{ocid: bk.ocid})
        MERGE (parent)-[r:OCI_VOLUME_BACKUP]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(link_block, backups=backups, oci_update_tag=oci_update_tag)

    link_boot = """
    UNWIND $backups AS bk
        WITH bk WHERE bk.source_kind = 'BOOT' AND bk.parent_volume_id IS NOT NULL
        MATCH (parent:OCIBootVolume{ocid: bk.parent_volume_id})
        MATCH (b:OCIVolumeBackup{ocid: bk.ocid})
        MERGE (parent)-[r:OCI_VOLUME_BACKUP]->(b)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(link_boot, backups=backups, oci_update_tag=oci_update_tag)


def sync_volume_backups(
    neo4j_session: neo4j.Session,
    blockstorage: oci.core.BlockstorageClient,
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    logger.debug(
        "Syncing OCI volume backups for compartment '%s', region '%s'.",
        compartment_id, region,
    )
    block_backups = get_volume_backup_list_data(blockstorage, compartment_id)["VolumeBackups"]
    boot_backups = get_boot_volume_backup_list_data(blockstorage, compartment_id)["BootVolumeBackups"]
    backups = transform_volume_backups(block_backups, boot_backups, region)
    if backups:
        load_volume_backups(neo4j_session, backups, oci_update_tag)


# ---------------------------------------------------------------------------
# File Storage (FSS): File Systems, Mount Targets, Exports
# ---------------------------------------------------------------------------

def get_file_system_list_data(
    file_storage: oci.file_storage.FileStorageClient,
    availability_domain: str,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List file systems in a compartment for an availability domain. See:
    https://docs.oracle.com/en-us/iaas/api/#/en/filestorage/latest/FileSystem/ListFileSystems
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            file_storage.list_file_systems,
            availability_domain=availability_domain,
            compartment_id=compartment_id,
        )
        return {'FileSystems': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve file systems for compartment '%s', AD '%s': %s",
            compartment_id, availability_domain, e.message,
        )
        return {'FileSystems': []}


def get_mount_target_list_data(
    file_storage: oci.file_storage.FileStorageClient,
    availability_domain: str,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List mount targets in a compartment for an availability domain. See:
    https://docs.oracle.com/en-us/iaas/api/#/en/filestorage/latest/MountTarget/ListMountTargets
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            file_storage.list_mount_targets,
            availability_domain=availability_domain,
            compartment_id=compartment_id,
        )
        return {'MountTargets': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve mount targets for compartment '%s', AD '%s': %s",
            compartment_id, availability_domain, e.message,
        )
        return {'MountTargets': []}


def get_export_list_data(
    file_storage: oci.file_storage.FileStorageClient,
    compartment_id: str,
    export_set_id: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List exports. ListExports can be filtered by compartment OR by export-set;
    we issue both perspectives so file-system-to-mount-target wiring is
    complete even when the mount target lives in a different compartment.
    """
    try:
        kwargs: Dict[str, Any] = {"compartment_id": compartment_id}
        if export_set_id:
            kwargs["export_set_id"] = export_set_id
        response = oci.pagination.list_call_get_all_results(
            file_storage.list_exports, **kwargs,
        )
        return {'Exports': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve FSS exports for compartment '%s': %s",
            compartment_id, e.message,
        )
        return {'Exports': []}


def transform_file_systems(
    file_systems: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for fs in file_systems:
        if not fs.get("id"):
            continue
        transformed.append({
            "ocid": fs.get("id"),
            "display_name": fs.get("display-name"),
            "compartment_id": fs.get("compartment-id"),
            "availability_domain": fs.get("availability-domain"),
            "lifecycle_state": fs.get("lifecycle-state"),
            "metered_bytes": fs.get("metered-bytes"),
            "kms_key_id": fs.get("kms-key-id"),
            "is_clone_parent": fs.get("is-clone-parent"),
            "is_hydrated": fs.get("is-hydrated"),
            "source_snapshot_id": fs.get("source-snapshot-id"),
            "parent_file_system_id": fs.get("parent-file-system-id"),
            "time_created": str(fs.get("time-created", "")),
            "region": region,
        })
    return transformed


def transform_mount_targets(
    mount_targets: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for mt in mount_targets:
        if not mt.get("id"):
            continue
        transformed.append({
            "ocid": mt.get("id"),
            "display_name": mt.get("display-name"),
            "compartment_id": mt.get("compartment-id"),
            "availability_domain": mt.get("availability-domain"),
            "lifecycle_state": mt.get("lifecycle-state"),
            "subnet_id": mt.get("subnet-id"),
            "export_set_id": mt.get("export-set-id"),
            "private_ip_ids": mt.get("private-ip-ids") or [],
            "nsg_ids": mt.get("nsg-ids") or [],
            "time_created": str(mt.get("time-created", "")),
            "region": region,
        })
    return transformed


def transform_exports(
    exports: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for ex in exports:
        if not ex.get("id"):
            continue
        transformed.append({
            "ocid": ex.get("id"),
            "path": ex.get("path"),
            "lifecycle_state": ex.get("lifecycle-state"),
            "file_system_id": ex.get("file-system-id"),
            "export_set_id": ex.get("export-set-id"),
            "time_created": str(ex.get("time-created", "")),
        })
    return transformed


def load_file_systems(
    neo4j_session: neo4j.Session,
    file_systems: List[Dict[str, Any]],
    compartment_id: str,
    oci_update_tag: int,
) -> None:
    ingest_fs = """
    UNWIND $file_systems AS fs
        MERGE (f:OCIFileSystem{ocid: fs.ocid})
        ON CREATE SET f.firstseen = timestamp(),
                      f.createdate = fs.time_created
        SET f.display_name = fs.display_name,
            f.compartment_id = fs.compartment_id,
            f.availability_domain = fs.availability_domain,
            f.lifecycle_state = fs.lifecycle_state,
            f.metered_bytes = fs.metered_bytes,
            f.kms_key_id = fs.kms_key_id,
            f.is_encrypted_with_cmk = (fs.kms_key_id IS NOT NULL),
            f.is_clone_parent = fs.is_clone_parent,
            f.is_hydrated = fs.is_hydrated,
            f.source_snapshot_id = fs.source_snapshot_id,
            f.parent_file_system_id = fs.parent_file_system_id,
            f.region = fs.region,
            f.lastupdated = $oci_update_tag
        WITH f
        MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
        MERGE (cc)-[r:RESOURCE]->(f)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(
        ingest_fs,
        file_systems=file_systems,
        COMPARTMENT_ID=compartment_id,
        oci_update_tag=oci_update_tag,
    )


def load_mount_targets(
    neo4j_session: neo4j.Session,
    mount_targets: List[Dict[str, Any]],
    compartment_id: str,
    oci_update_tag: int,
) -> None:
    ingest_mt = """
    UNWIND $mount_targets AS mt
        MERGE (m:OCIMountTarget{ocid: mt.ocid})
        ON CREATE SET m.firstseen = timestamp(),
                      m.createdate = mt.time_created
        SET m.display_name = mt.display_name,
            m.compartment_id = mt.compartment_id,
            m.availability_domain = mt.availability_domain,
            m.lifecycle_state = mt.lifecycle_state,
            m.subnet_id = mt.subnet_id,
            m.export_set_id = mt.export_set_id,
            m.private_ip_ids = mt.private_ip_ids,
            m.nsg_ids = mt.nsg_ids,
            m.region = mt.region,
            m.lastupdated = $oci_update_tag
        WITH m
        MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
        MERGE (cc)-[r:RESOURCE]->(m)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(
        ingest_mt,
        mount_targets=mount_targets,
        COMPARTMENT_ID=compartment_id,
        oci_update_tag=oci_update_tag,
    )


def load_exports(
    neo4j_session: neo4j.Session,
    exports: List[Dict[str, Any]],
    oci_update_tag: int,
) -> None:
    """
    Connect file systems to mount targets via the export set. The graph edge
    is intentionally direct: ``(:OCIMountTarget)-[:OCI_EXPORT]->(:OCIFileSystem)``
    with the export's NFS path as a relationship property, so consumers can
    reason about reachability without traversing an export-set node.
    """
    ingest_exports = """
    UNWIND $exports AS ex
        WITH ex WHERE ex.export_set_id IS NOT NULL AND ex.file_system_id IS NOT NULL
        MATCH (mt:OCIMountTarget{export_set_id: ex.export_set_id})
        MATCH (fs:OCIFileSystem{ocid: ex.file_system_id})
        MERGE (mt)-[r:OCI_EXPORT{ocid: ex.ocid}]->(fs)
        ON CREATE SET r.firstseen = timestamp()
        SET r.path = ex.path,
            r.lifecycle_state = ex.lifecycle_state,
            r.createdate = ex.time_created,
            r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(ingest_exports, exports=exports, oci_update_tag=oci_update_tag)


def link_instances_to_file_systems(
    neo4j_session: neo4j.Session,
    oci_update_tag: int,
) -> None:
    """
    Heuristic placeholder: OCI exposes no first-party API to enumerate which
    instances have actually mounted which file system (NFS mount state lives
    in the guest OS). As a best-effort signal we connect any instance whose
    VNIC sits on the same subnet as a mount target that exports a given file
    system. Treat this as a reachability hint, not a confirmed mount.

    TODO: replace with authoritative OS-agent or OS Management Hub data
    once that ingestion path lands.
    """
    link_query = """
    MATCH (mt:OCIMountTarget)-[:OCI_EXPORT]->(fs:OCIFileSystem)
    MATCH (inst:OCIInstance)-[:OCI_VNIC_ATTACHMENT]->(vnic:OCIVnicAttachment)
    WHERE vnic.subnet_id IS NOT NULL
      AND vnic.subnet_id = mt.subnet_id
    MERGE (inst)-[r:MOUNTS]->(fs)
    ON CREATE SET r.firstseen = timestamp(),
                  r.inferred = true,
                  r.inference_method = 'shared_subnet'
    SET r.lastupdated = $oci_update_tag
    """
    neo4j_session.run(link_query, oci_update_tag=oci_update_tag)


def sync_file_storage(
    neo4j_session: neo4j.Session,
    file_storage: oci.file_storage.FileStorageClient,
    tenancy_id: str,
    compartment_id: str,
    availability_domains: List[str],
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Sync File Storage Service: file systems, mount targets, exports, and the
    heuristic instance→file-system MOUNTS edge.
    """
    logger.debug(
        "Syncing OCI File Storage for compartment '%s', region '%s'.",
        compartment_id, region,
    )

    fs_raw: List[Dict[str, Any]] = []
    mt_raw: List[Dict[str, Any]] = []
    for ad in availability_domains:
        fs_raw.extend(get_file_system_list_data(file_storage, ad, compartment_id)["FileSystems"])
        mt_raw.extend(get_mount_target_list_data(file_storage, ad, compartment_id)["MountTargets"])

    file_systems = transform_file_systems(fs_raw, region)
    mount_targets = transform_mount_targets(mt_raw, region)

    if file_systems:
        load_file_systems(neo4j_session, file_systems, compartment_id, oci_update_tag)
    if mount_targets:
        load_mount_targets(neo4j_session, mount_targets, compartment_id, oci_update_tag)

    # Pull exports compartment-wide, then transform & load.
    exports_raw = get_export_list_data(file_storage, compartment_id)["Exports"]
    exports = transform_exports(exports_raw)
    if exports:
        load_exports(neo4j_session, exports, oci_update_tag)

    # Best-effort instance → file system connectivity inference.
    link_instances_to_file_systems(neo4j_session, oci_update_tag)


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    run_cleanup_job(
        'oci_import_storage_cleanup.json', neo4j_session, common_job_parameters,
    )


# ---------------------------------------------------------------------------
# Entry point: ``sync`` follows the OCI orchestrator's expected signature
# (neo4j_session, client, tenancy_id, oci_update_tag, common_job_parameters,
# regions). ``client`` here is the bundled ``OCIStorageClients`` object.
# ---------------------------------------------------------------------------

def sync(
    neo4j_session: neo4j.Session,
    storage_clients: OCIStorageClients,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: Optional[List[str]] = None,
) -> None:
    compartment_id = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    logger.info("Syncing OCI Storage for compartment '%s'.", compartment_id)

    if not regions:
        regions = [storage_clients.blockstorage.base_client.region or ""]

    # Build a one-off identity client to enumerate availability domains
    # without forcing the orchestrator to thread one through. We re-use the
    # blockstorage client's signer/config to keep auth identical.
    identity_client: Optional[oci.identity.identity_client.IdentityClient]
    try:
        identity_client = oci.identity.IdentityClient(
            config={}, signer=storage_clients.blockstorage.base_client.signer,
        )
    except Exception:  # pragma: no cover - best effort
        identity_client = None

    for region in regions:
        logger.info(
            "Syncing OCI Storage in region '%s' for compartment '%s'.",
            region, compartment_id,
        )
        storage_clients.set_region(region)
        if identity_client is not None:
            try:
                identity_client.base_client.set_region(region)
            except Exception:  # pragma: no cover
                pass

        availability_domains = get_availability_domains(identity_client, compartment_id)

        # Object Storage
        try:
            sync_buckets(
                neo4j_session, storage_clients.object_storage,
                tenancy_id, compartment_id, region, oci_update_tag,
            )
        except Exception as e:
            logger.error("Error syncing OCI Object Storage buckets: %s", e, exc_info=True)

        # Block Volumes
        try:
            sync_block_volumes(
                neo4j_session, storage_clients.blockstorage,
                tenancy_id, compartment_id, region, oci_update_tag,
            )
        except Exception as e:
            logger.error("Error syncing OCI block volumes: %s", e, exc_info=True)

        # Boot Volumes
        try:
            sync_boot_volumes(
                neo4j_session, storage_clients.blockstorage,
                tenancy_id, compartment_id, availability_domains,
                region, oci_update_tag,
            )
        except Exception as e:
            logger.error("Error syncing OCI boot volumes: %s", e, exc_info=True)

        # Volume Backups (block + boot)
        try:
            sync_volume_backups(
                neo4j_session, storage_clients.blockstorage,
                tenancy_id, compartment_id, region, oci_update_tag,
            )
        except Exception as e:
            logger.error("Error syncing OCI volume backups: %s", e, exc_info=True)

        # File Storage
        try:
            sync_file_storage(
                neo4j_session, storage_clients.file_storage,
                tenancy_id, compartment_id, availability_domains,
                region, oci_update_tag,
            )
        except Exception as e:
            logger.error("Error syncing OCI File Storage: %s", e, exc_info=True)

    cleanup(neo4j_session, common_job_parameters)
