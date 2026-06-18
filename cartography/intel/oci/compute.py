# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Compute API-centric functions
# https://docs.cloud.oracle.com/iaas/Content/Compute/Concepts/computeoverview.htm
import logging
import time
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci
import oci.core
import oci.identity

from . import utils
from cartography.util import run_cleanup_job

logger = logging.getLogger(__name__)


def get_instance_list_data(
    compute: oci.core.compute_client.ComputeClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all compute instances in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Instance/ListInstances
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            compute.list_instances, compartment_id=compartment_id,
        )
        return {'Instances': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve compute instances for compartment '%s': %s", compartment_id, e.message,
        )
        return {'Instances': []}


def load_instances(
    neo4j_session: neo4j.Session,
    instances: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Compute Instance data into Neo4j.
    """
    ingest_instance = """
    MERGE (inode:OCIInstance{id: $OCID})
    ON CREATE SET inode.firstseen = timestamp(),
    inode.createdate = $TIME_CREATED
    SET inode.ocid = $OCID,
    inode.display_name = $DISPLAY_NAME,
    inode.compartment_id = $COMPARTMENT_ID,
    inode.resource_type = 'oci-compute-vm-instance',
    inode.availability_domain = $AVAILABILITY_DOMAIN,
    inode.fault_domain = $FAULT_DOMAIN,
    inode.shape = $SHAPE,
    inode.lifecycle_state = $LIFECYCLE_STATE,
    inode.region = $REGION,
    inode.image_id = $IMAGE_ID,
    inode.are_legacy_imds_endpoints_disabled = $ARE_LEGACY_IMDS_ENDPOINTS_DISABLED,
    inode.is_secure_boot_enabled = $IS_SECURE_BOOT_ENABLED,
    inode.is_pv_encryption_in_transit_enabled = $IS_PV_ENCRYPTION_IN_TRANSIT_ENABLED,
    inode.is_monitoring_disabled = $IS_MONITORING_DISABLED,
    inode.lastupdated = $oci_update_tag
    WITH inode
    MATCH (cc:OCICompartment{id: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(inode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for instance in instances:
        # Nested config objects (may be absent depending on shape/image).
        instance_options = instance.get("instance-options", {}) or {}
        platform_config = instance.get("platform-config", {}) or {}
        launch_options = instance.get("launch-options", {}) or {}
        agent_config = instance.get("agent-config", {}) or {}

        neo4j_session.run(
            ingest_instance,
            OCID=instance.get("id"),
            DISPLAY_NAME=instance.get("display-name"),
            COMPARTMENT_ID=instance.get("compartment-id", compartment_id),
            AVAILABILITY_DOMAIN=instance.get("availability-domain"),
            FAULT_DOMAIN=instance.get("fault-domain"),
            SHAPE=instance.get("shape"),
            LIFECYCLE_STATE=instance.get("lifecycle-state"),
            REGION=region,
            IMAGE_ID=instance.get("image-id"),
            ARE_LEGACY_IMDS_ENDPOINTS_DISABLED=instance_options.get("are-legacy-imds-endpoints-disabled"),
            IS_SECURE_BOOT_ENABLED=platform_config.get("is-secure-boot-enabled"),
            IS_PV_ENCRYPTION_IN_TRANSIT_ENABLED=launch_options.get("is-pv-encryption-in-transit-enabled"),
            IS_MONITORING_DISABLED=agent_config.get("is-monitoring-disabled"),
            TIME_CREATED=str(instance.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def get_vnic_attachment_list_data(
    compute: oci.core.compute_client.ComputeClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all VNIC attachments in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/VnicAttachment/ListVnicAttachments
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            compute.list_vnic_attachments, compartment_id=compartment_id,
        )
        return {'VnicAttachments': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve VNIC attachments for compartment '%s': %s", compartment_id, e.message,
        )
        return {'VnicAttachments': []}


def load_vnic_attachments(
    neo4j_session: neo4j.Session,
    vnic_attachments: List[Dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI VNIC Attachment data into Neo4j and link to instances.
    """
    ingest_vnic_attachment = """
    MERGE (vnic:OCIVnicAttachment{id: $OCID})
    ON CREATE SET vnic.firstseen = timestamp(),
    vnic.createdate = $TIME_CREATED
    SET vnic.ocid = $OCID,
    vnic.display_name = $DISPLAY_NAME,
    vnic.compartment_id = $COMPARTMENT_ID,
    vnic.availability_domain = $AVAILABILITY_DOMAIN,
    vnic.lifecycle_state = $LIFECYCLE_STATE,
    vnic.vnic_id = $VNIC_ID,
    vnic.subnet_id = $SUBNET_ID,
    vnic.nic_index = $NIC_INDEX,
    vnic.lastupdated = $oci_update_tag
    WITH vnic
    MATCH (inode:OCIInstance{id: $INSTANCE_ID})
    MERGE (inode)-[r:OCI_VNIC_ATTACHMENT]->(vnic)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for attachment in vnic_attachments:
        neo4j_session.run(
            ingest_vnic_attachment,
            OCID=attachment.get("id"),
            DISPLAY_NAME=attachment.get("display-name"),
            COMPARTMENT_ID=attachment.get("compartment-id"),
            AVAILABILITY_DOMAIN=attachment.get("availability-domain"),
            LIFECYCLE_STATE=attachment.get("lifecycle-state"),
            VNIC_ID=attachment.get("vnic-id"),
            SUBNET_ID=attachment.get("subnet-id"),
            NIC_INDEX=attachment.get("nic-index"),
            INSTANCE_ID=attachment.get("instance-id"),
            TIME_CREATED=str(attachment.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def get_image_list_data(
    compute: oci.core.compute_client.ComputeClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all images in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Image/ListImages
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            compute.list_images, compartment_id=compartment_id,
        )
        return {'Images': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve images for compartment '%s': %s", compartment_id, e.message,
        )
        return {'Images': []}


def load_images(
    neo4j_session: neo4j.Session,
    images: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Image data into Neo4j.
    """
    ingest_image = """
    MERGE (img:OCIImage{id: $OCID})
    ON CREATE SET img.firstseen = timestamp(),
    img.createdate = $TIME_CREATED
    SET img.ocid = $OCID,
    img.display_name = $DISPLAY_NAME,
    img.compartment_id = $COMPARTMENT_ID,
    img.operating_system = $OPERATING_SYSTEM,
    img.operating_system_version = $OPERATING_SYSTEM_VERSION,
    img.lifecycle_state = $LIFECYCLE_STATE,
    img.size_in_mbs = $SIZE_IN_MBS,
    img.lastupdated = $oci_update_tag
    WITH img
    MATCH (cc:OCICompartment{id: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(img)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for image in images:
        neo4j_session.run(
            ingest_image,
            OCID=image.get("id"),
            DISPLAY_NAME=image.get("display-name"),
            COMPARTMENT_ID=image.get("compartment-id") if image.get("compartment-id") else compartment_id,
            OPERATING_SYSTEM=image.get("operating-system"),
            OPERATING_SYSTEM_VERSION=image.get("operating-system-version"),
            LIFECYCLE_STATE=image.get("lifecycle-state"),
            SIZE_IN_MBS=image.get("size-in-mbs"),
            TIME_CREATED=str(image.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def get_boot_volume_attachment_list_data(
    compute: oci.core.compute_client.ComputeClient,
    availability_domain: str,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all boot volume attachments in a compartment for a given availability domain.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/BootVolumeAttachment/ListBootVolumeAttachments
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            compute.list_boot_volume_attachments,
            availability_domain=availability_domain,
            compartment_id=compartment_id,
        )
        return {'BootVolumeAttachments': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve boot volume attachments for compartment '%s', AD '%s': %s",
            compartment_id, availability_domain, e.message,
        )
        return {'BootVolumeAttachments': []}


def load_boot_volume_attachments(
    neo4j_session: neo4j.Session,
    boot_volume_attachments: List[Dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Boot Volume Attachment data into Neo4j and link to instances.
    """
    ingest_boot_volume_attachment = """
    MERGE (bva:OCIBootVolumeAttachment{id: $OCID})
    ON CREATE SET bva.firstseen = timestamp(),
    bva.createdate = $TIME_CREATED
    SET bva.ocid = $OCID,
    bva.display_name = $DISPLAY_NAME,
    bva.compartment_id = $COMPARTMENT_ID,
    bva.availability_domain = $AVAILABILITY_DOMAIN,
    bva.lifecycle_state = $LIFECYCLE_STATE,
    bva.boot_volume_id = $BOOT_VOLUME_ID,
    bva.lastupdated = $oci_update_tag
    WITH bva
    MATCH (inode:OCIInstance{id: $INSTANCE_ID})
    MERGE (inode)-[r:OCI_BOOT_VOLUME_ATTACHMENT]->(bva)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for attachment in boot_volume_attachments:
        neo4j_session.run(
            ingest_boot_volume_attachment,
            OCID=attachment.get("id"),
            DISPLAY_NAME=attachment.get("display-name"),
            COMPARTMENT_ID=attachment.get("compartment-id"),
            AVAILABILITY_DOMAIN=attachment.get("availability-domain"),
            LIFECYCLE_STATE=attachment.get("lifecycle-state"),
            BOOT_VOLUME_ID=attachment.get("boot-volume-id"),
            INSTANCE_ID=attachment.get("instance-id"),
            TIME_CREATED=str(attachment.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def get_volume_attachment_list_data(
    compute: oci.core.compute_client.ComputeClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all volume attachments in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/VolumeAttachment/ListVolumeAttachments
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            compute.list_volume_attachments, compartment_id=compartment_id,
        )
        return {'VolumeAttachments': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve volume attachments for compartment '%s': %s", compartment_id, e.message,
        )
        return {'VolumeAttachments': []}


def load_volume_attachments(
    neo4j_session: neo4j.Session,
    volume_attachments: List[Dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Volume Attachment data into Neo4j and link to instances.
    """
    ingest_volume_attachment = """
    MERGE (va:OCIVolumeAttachment{id: $OCID})
    ON CREATE SET va.firstseen = timestamp(),
    va.createdate = $TIME_CREATED
    SET va.ocid = $OCID,
    va.display_name = $DISPLAY_NAME,
    va.compartment_id = $COMPARTMENT_ID,
    va.availability_domain = $AVAILABILITY_DOMAIN,
    va.lifecycle_state = $LIFECYCLE_STATE,
    va.volume_id = $VOLUME_ID,
    va.attachment_type = $ATTACHMENT_TYPE,
    va.is_read_only = $IS_READ_ONLY,
    va.lastupdated = $oci_update_tag
    WITH va
    MATCH (inode:OCIInstance{id: $INSTANCE_ID})
    MERGE (inode)-[r:OCI_VOLUME_ATTACHMENT]->(va)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for attachment in volume_attachments:
        neo4j_session.run(
            ingest_volume_attachment,
            OCID=attachment.get("id"),
            DISPLAY_NAME=attachment.get("display-name"),
            COMPARTMENT_ID=attachment.get("compartment-id"),
            AVAILABILITY_DOMAIN=attachment.get("availability-domain"),
            LIFECYCLE_STATE=attachment.get("lifecycle-state"),
            VOLUME_ID=attachment.get("volume-id"),
            ATTACHMENT_TYPE=attachment.get("attachment-type"),
            IS_READ_ONLY=attachment.get("is-read-only"),
            INSTANCE_ID=attachment.get("instance-id"),
            TIME_CREATED=str(attachment.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def get_availability_domains(
    identity: oci.identity.identity_client.IdentityClient,
    compartment_id: str,
) -> List[str]:
    """
    Get the names of all availability domains in a compartment. Block/boot volume
    listing is scoped per availability domain.
    See https://docs.oracle.com/en-us/iaas/api/#/en/identity/latest/AvailabilityDomain/ListAvailabilityDomains
    """
    try:
        response = identity.list_availability_domains(compartment_id=compartment_id)
        return [ad.name for ad in response.data]
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve availability domains for compartment '%s': %s", compartment_id, e.message,
        )
        return []


def get_boot_volume_list_data(
    blockstorage: oci.core.blockstorage_client.BlockstorageClient,
    availability_domain: str,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all boot volumes in a compartment for a given availability domain.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/BootVolume/ListBootVolumes
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


def has_backup_policy_assigned(
    blockstorage: oci.core.blockstorage_client.BlockstorageClient,
    volume_id: str,
) -> bool:
    """
    Return True if the given volume (boot or block) has a backup policy assigned.
    Uses BlockstorageClient.get_volume_backup_policy_asset_assignment (asset_id = volume OCID).
    """
    if not volume_id:
        return False
    try:
        response = blockstorage.get_volume_backup_policy_asset_assignment(asset_id=volume_id)
        return bool(response.data)
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve backup policy assignment for volume '%s': %s", volume_id, e.message,
        )
        return False


def load_boot_volumes(
    neo4j_session: neo4j.Session,
    boot_volumes: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Boot Volume data into Neo4j, link to its compartment, and link to the
    owning instance via its boot volume attachment.
    """
    ingest_boot_volume = """
    MERGE (bv:OCIBootVolume{ocid: $OCID})
    ON CREATE SET bv.firstseen = timestamp(),
    bv.createdate = $TIME_CREATED
    SET bv.display_name = $DISPLAY_NAME,
    bv.compartment_id = $COMPARTMENT_ID,
    bv.resource_type = 'oci-storage-blockstorage-bootvolume',
    bv.availability_domain = $AVAILABILITY_DOMAIN,
    bv.lifecycle_state = $LIFECYCLE_STATE,
    bv.size_in_gbs = $SIZE_IN_GBS,
    bv.kms_key_id = $KMS_KEY_ID,
    bv.is_hydrated = $IS_HYDRATED,
    bv.vpus_per_gb = $VPUS_PER_GB,
    bv.image_id = $IMAGE_ID,
    bv.has_backup_policy = $HAS_BACKUP_POLICY,
    bv.region = $REGION,
    bv.lastupdated = $oci_update_tag
    WITH bv
    MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(bv)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    WITH bv
    OPTIONAL MATCH (inode:OCIInstance)-[:OCI_BOOT_VOLUME_ATTACHMENT]->(:OCIBootVolumeAttachment{boot_volume_id: $OCID})
    FOREACH (_ IN CASE WHEN inode IS NULL THEN [] ELSE [1] END |
        MERGE (inode)-[ri:OCI_BOOT_VOLUME]->(bv)
        ON CREATE SET ri.firstseen = timestamp()
        SET ri.lastupdated = $oci_update_tag
    )
    """

    for volume in boot_volumes:
        neo4j_session.run(
            ingest_boot_volume,
            OCID=volume.get("id"),
            DISPLAY_NAME=volume.get("display-name"),
            COMPARTMENT_ID=volume.get("compartment-id", compartment_id),
            AVAILABILITY_DOMAIN=volume.get("availability-domain", ""),
            LIFECYCLE_STATE=volume.get("lifecycle-state"),
            SIZE_IN_GBS=volume.get("size-in-gbs"),
            KMS_KEY_ID=volume.get("kms-key-id", ""),
            IS_HYDRATED=volume.get("is-hydrated"),
            VPUS_PER_GB=volume.get("vpus-per-gb"),
            IMAGE_ID=volume.get("image-id", ""),
            HAS_BACKUP_POLICY=volume.get("_has_backup_policy", False),
            REGION=region,
            TIME_CREATED=str(volume.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def get_block_volume_list_data(
    blockstorage: oci.core.blockstorage_client.BlockstorageClient,
    compartment_id: str,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all block volumes in a compartment.
    See https://docs.oracle.com/en-us/iaas/api/#/en/iaas/latest/Volume/ListVolumes
    """
    try:
        response = oci.pagination.list_call_get_all_results(
            blockstorage.list_volumes, compartment_id=compartment_id,
        )
        return {'Volumes': utils.oci_object_to_json(response.data)}
    except oci.exceptions.ServiceError as e:
        logger.warning(
            "Could not retrieve block volumes for compartment '%s': %s", compartment_id, e.message,
        )
        return {'Volumes': []}


def load_block_volumes(
    neo4j_session: neo4j.Session,
    block_volumes: List[Dict[str, Any]],
    tenancy_id: str,
    compartment_id: str,
    region: str,
    oci_update_tag: int,
) -> None:
    """
    Ingest OCI Block Volume data into Neo4j, link to its compartment, and create an
    ATTACHED_TO relationship to the instance via its volume attachment.
    """
    ingest_block_volume = """
    MERGE (bv:OCIBlockVolume{ocid: $OCID})
    ON CREATE SET bv.firstseen = timestamp(),
    bv.createdate = $TIME_CREATED
    SET bv.display_name = $DISPLAY_NAME,
    bv.compartment_id = $COMPARTMENT_ID,
    bv.resource_type = 'oci-storage-blockstorage-volume',
    bv.availability_domain = $AVAILABILITY_DOMAIN,
    bv.lifecycle_state = $LIFECYCLE_STATE,
    bv.size_in_gbs = $SIZE_IN_GBS,
    bv.kms_key_id = $KMS_KEY_ID,
    bv.is_hydrated = $IS_HYDRATED,
    bv.vpus_per_gb = $VPUS_PER_GB,
    bv.has_backup_policy = $HAS_BACKUP_POLICY,
    bv.region = $REGION,
    bv.lastupdated = $oci_update_tag
    WITH bv
    MATCH (cc:OCICompartment{ocid: $COMPARTMENT_ID})
    MERGE (cc)-[r:RESOURCE]->(bv)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    WITH bv
    OPTIONAL MATCH (inode:OCIInstance)-[:OCI_VOLUME_ATTACHMENT]->(:OCIVolumeAttachment{volume_id: $OCID})
    FOREACH (_ IN CASE WHEN inode IS NULL THEN [] ELSE [1] END |
        MERGE (bv)-[ri:ATTACHED_TO]->(inode)
        ON CREATE SET ri.firstseen = timestamp()
        SET ri.lastupdated = $oci_update_tag
    )
    """

    for volume in block_volumes:
        neo4j_session.run(
            ingest_block_volume,
            OCID=volume.get("id"),
            DISPLAY_NAME=volume.get("display-name"),
            COMPARTMENT_ID=volume.get("compartment-id", compartment_id),
            AVAILABILITY_DOMAIN=volume.get("availability-domain", ""),
            LIFECYCLE_STATE=volume.get("lifecycle-state"),
            SIZE_IN_GBS=volume.get("size-in-gbs"),
            KMS_KEY_ID=volume.get("kms-key-id", ""),
            IS_HYDRATED=volume.get("is-hydrated"),
            VPUS_PER_GB=volume.get("vpus-per-gb"),
            HAS_BACKUP_POLICY=volume.get("_has_backup_policy", False),
            REGION=region,
            TIME_CREATED=str(volume.get("time-created", "")),
            oci_update_tag=oci_update_tag,
        )


def sync_boot_volume_attachments(
    neo4j_session: neo4j.Session,
    compute: oci.core.compute_client.ComputeClient,
    availability_domains: List[str],
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all boot volume attachments across compartments and availability domains.
    """
    logger.debug("Syncing OCI boot volume attachments for tenancy '%s'.", tenancy_id)
    for compartment in compartments:
        for availability_domain in availability_domains:
            data = get_boot_volume_attachment_list_data(compute, availability_domain, compartment["ocid"])
            if data["BootVolumeAttachments"]:
                load_boot_volume_attachments(
                    neo4j_session, data["BootVolumeAttachments"], tenancy_id, oci_update_tag,
                )


def sync_boot_volumes(
    neo4j_session: neo4j.Session,
    blockstorage: oci.core.blockstorage_client.BlockstorageClient,
    availability_domains: List[str],
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all boot volumes across compartments and availability domains, enriching each
    with whether a backup policy is assigned.
    """
    logger.debug("Syncing OCI boot volumes for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        for availability_domain in availability_domains:
            data = get_boot_volume_list_data(blockstorage, availability_domain, compartment["ocid"])
            for volume in data["BootVolumes"]:
                volume["_has_backup_policy"] = has_backup_policy_assigned(blockstorage, volume.get("id"))
            if data["BootVolumes"]:
                load_boot_volumes(
                    neo4j_session, data["BootVolumes"], tenancy_id, compartment["ocid"], region, oci_update_tag,
                )


def sync_block_volumes(
    neo4j_session: neo4j.Session,
    blockstorage: oci.core.blockstorage_client.BlockstorageClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all block volumes across compartments, enriching each with whether a backup
    policy is assigned.
    """
    logger.debug("Syncing OCI block volumes for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_block_volume_list_data(blockstorage, compartment["ocid"])
        for volume in data["Volumes"]:
            volume["_has_backup_policy"] = has_backup_policy_assigned(blockstorage, volume.get("id"))
        if data["Volumes"]:
            load_block_volumes(
                neo4j_session, data["Volumes"], tenancy_id, compartment["ocid"], region, oci_update_tag,
            )


def sync_instances(
    neo4j_session: neo4j.Session,
    compute: oci.core.compute_client.ComputeClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    region: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all compute instances across all compartments in the tenancy.
    """
    tic = time.perf_counter()
    logger.debug("Syncing OCI compute instances for tenancy '%s', region '%s'.", tenancy_id, region)
    total = 0
    for compartment in compartments:
        data = get_instance_list_data(compute, compartment["ocid"])
        if data["Instances"]:
            total += len(data["Instances"])
            load_instances(neo4j_session, data["Instances"], tenancy_id, compartment["ocid"], region, oci_update_tag)
    logger.info(f"Time to process OCI compute instances for tenancy '{tenancy_id}' region '{region}' ({total} instances): {time.perf_counter() - tic:0.4f} seconds")


def sync_vnic_attachments(
    neo4j_session: neo4j.Session,
    compute: oci.core.compute_client.ComputeClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all VNIC attachments across all compartments in the tenancy.
    """
    tic = time.perf_counter()
    logger.debug("Syncing OCI VNIC attachments for tenancy '%s'.", tenancy_id)
    total = 0
    for compartment in compartments:
        data = get_vnic_attachment_list_data(compute, compartment["ocid"])
        if data["VnicAttachments"]:
            total += len(data["VnicAttachments"])
            load_vnic_attachments(neo4j_session, data["VnicAttachments"], tenancy_id, oci_update_tag)
    logger.info(f"Time to process OCI VNIC attachments for tenancy '{tenancy_id}' ({total} attachments): {time.perf_counter() - tic:0.4f} seconds")


def sync_images(
    neo4j_session: neo4j.Session,
    compute: oci.core.compute_client.ComputeClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all images across all compartments in the tenancy.
    """
    tic = time.perf_counter()
    logger.debug("Syncing OCI images for tenancy '%s'.", tenancy_id)
    total = 0
    for compartment in compartments:
        data = get_image_list_data(compute, compartment["ocid"])
        if data["Images"]:
            total += len(data["Images"])
            load_images(neo4j_session, data["Images"], tenancy_id, compartment["ocid"], oci_update_tag)
    logger.info(f"Time to process OCI images for tenancy '{tenancy_id}' ({total} images): {time.perf_counter() - tic:0.4f} seconds")


def sync_volume_attachments(
    neo4j_session: neo4j.Session,
    compute: oci.core.compute_client.ComputeClient,
    compartments: List[Dict[str, Any]],
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync all volume attachments across all compartments in the tenancy.
    """
    tic = time.perf_counter()
    logger.debug("Syncing OCI volume attachments for tenancy '%s'.", tenancy_id)
    total = 0
    for compartment in compartments:
        data = get_volume_attachment_list_data(compute, compartment["ocid"])
        if data["VolumeAttachments"]:
            total += len(data["VolumeAttachments"])
            load_volume_attachments(neo4j_session, data["VolumeAttachments"], tenancy_id, oci_update_tag)
    logger.info(f"Time to process OCI volume attachments for tenancy '{tenancy_id}' ({total} attachments): {time.perf_counter() - tic:0.4f} seconds")


def sync(
    neo4j_session: neo4j.Session,
    compute: oci.core.compute_client.ComputeClient,
    tenancy_id: str,
    oci_update_tag: int,
    common_job_parameters: Dict[str, Any],
    regions: List[str] = None,
) -> None:
    """
    Sync OCI Compute resources for the compartment specified in common_job_parameters.
    """
    tic = time.perf_counter()
    compartment_ocid = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    logger.info("Syncing OCI Compute for compartment '%s'.", compartment_ocid)

    # Use only the target compartment for resource listing
    compartments = [{"ocid": compartment_ocid, "name": "target", "compartmentid": tenancy_id}]

    # If no regions provided, use the compute client's current region
    if not regions:
        regions = [compute.base_client.region or ""]

    # Block storage (boot/block volumes) and identity (availability domains) live on
    # separate clients. Reuse the compute client's config/signer so we authenticate
    # identically.
    blockstorage = oci.core.BlockstorageClient(
        config=compute.base_client.config,
        signer=getattr(compute.base_client, "signer", None),
    )
    identity = oci.identity.IdentityClient(
        config=compute.base_client.config,
        signer=getattr(compute.base_client, "signer", None),
    )

    for region in regions:
        logger.info("Syncing OCI Compute in region '%s' for compartment '%s'.", region, compartment_ocid)
        compute.base_client.set_region(region)
        blockstorage.base_client.set_region(region)
        identity.base_client.set_region(region)

        # Availability domains are needed to scope boot volume / boot volume attachment listing.
        availability_domains: List[str] = []
        for compartment in compartments:
            availability_domains.extend(get_availability_domains(identity, compartment["ocid"]))
        # De-duplicate while preserving order.
        availability_domains = list(dict.fromkeys(availability_domains))

        # Sync instances
        sync_instances(neo4j_session, compute, compartments, tenancy_id, region, oci_update_tag, common_job_parameters)

        # Sync VNIC attachments (links instances to network interfaces)
        sync_vnic_attachments(neo4j_session, compute, compartments, tenancy_id, oci_update_tag, common_job_parameters)

        # Sync images
        sync_images(neo4j_session, compute, compartments, tenancy_id, oci_update_tag, common_job_parameters)

        # Sync boot volume attachments (links instances to boot volumes)
        sync_boot_volume_attachments(
            neo4j_session, compute, availability_domains, compartments, tenancy_id,
            oci_update_tag, common_job_parameters,
        )

        # Sync volume attachments (block volumes attached to instances)
        sync_volume_attachments(neo4j_session, compute, compartments, tenancy_id, oci_update_tag, common_job_parameters)

        # Sync boot volumes (with kms_key_id + has_backup_policy; links to instance)
        sync_boot_volumes(
            neo4j_session, blockstorage, availability_domains, compartments, tenancy_id,
            region, oci_update_tag, common_job_parameters,
        )

        # Sync block volumes (with kms_key_id + has_backup_policy; ATTACHED_TO instance)
        sync_block_volumes(
            neo4j_session, blockstorage, compartments, tenancy_id, region, oci_update_tag, common_job_parameters,
        )

    # Cleanup stale nodes
    run_cleanup_job('oci_import_compute_instances_cleanup.json', neo4j_session, common_job_parameters)
    toc = time.perf_counter()
    logger.info(f"Time to process OCI Compute for tenancy '{tenancy_id}': {toc - tic:0.4f} seconds")
