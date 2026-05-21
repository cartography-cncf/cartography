# Copyright (c) 2020, Oracle and/or its affiliates.
# OCI Compute API-centric functions
# https://docs.cloud.oracle.com/iaas/Content/Compute/Concepts/computeoverview.htm
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import oci

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
    MERGE (inode:OCIInstance{ocid: $OCID})
    ON CREATE SET inode.firstseen = timestamp(),
    inode.createdate = $TIME_CREATED
    SET inode.display_name = $DISPLAY_NAME,
    inode.compartment_id = $COMPARTMENT_ID,
    inode.availability_domain = $AVAILABILITY_DOMAIN,
    inode.fault_domain = $FAULT_DOMAIN,
    inode.shape = $SHAPE,
    inode.lifecycle_state = $LIFECYCLE_STATE,
    inode.region = $REGION,
    inode.image_id = $IMAGE_ID,
    inode.lastupdated = $oci_update_tag
    WITH inode
    MATCH (cc) WHERE (cc:OCICompartment OR cc:OCITenancy) AND cc.ocid=$COMPARTMENT_ID
    MERGE (cc)-[r:RESOURCE]->(inode)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for instance in instances:
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
    MERGE (vnic:OCIVnicAttachment{ocid: $OCID})
    ON CREATE SET vnic.firstseen = timestamp(),
    vnic.createdate = $TIME_CREATED
    SET vnic.display_name = $DISPLAY_NAME,
    vnic.compartment_id = $COMPARTMENT_ID,
    vnic.availability_domain = $AVAILABILITY_DOMAIN,
    vnic.lifecycle_state = $LIFECYCLE_STATE,
    vnic.vnic_id = $VNIC_ID,
    vnic.subnet_id = $SUBNET_ID,
    vnic.nic_index = $NIC_INDEX,
    vnic.lastupdated = $oci_update_tag
    WITH vnic
    MATCH (inode:OCIInstance{ocid: $INSTANCE_ID})
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
    MERGE (img:OCIImage{ocid: $OCID})
    ON CREATE SET img.firstseen = timestamp(),
    img.createdate = $TIME_CREATED
    SET img.display_name = $DISPLAY_NAME,
    img.compartment_id = $COMPARTMENT_ID,
    img.operating_system = $OPERATING_SYSTEM,
    img.operating_system_version = $OPERATING_SYSTEM_VERSION,
    img.lifecycle_state = $LIFECYCLE_STATE,
    img.size_in_mbs = $SIZE_IN_MBS,
    img.lastupdated = $oci_update_tag
    WITH img
    MATCH (cc) WHERE (cc:OCICompartment OR cc:OCITenancy) AND cc.ocid=$COMPARTMENT_ID
    MERGE (cc)-[r:RESOURCE]->(img)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $oci_update_tag
    """

    for image in images:
        neo4j_session.run(
            ingest_image,
            OCID=image.get("id"),
            DISPLAY_NAME=image.get("display-name"),
            COMPARTMENT_ID=image.get("compartment-id", compartment_id),
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
    MERGE (bva:OCIBootVolumeAttachment{ocid: $OCID})
    ON CREATE SET bva.firstseen = timestamp(),
    bva.createdate = $TIME_CREATED
    SET bva.display_name = $DISPLAY_NAME,
    bva.compartment_id = $COMPARTMENT_ID,
    bva.availability_domain = $AVAILABILITY_DOMAIN,
    bva.lifecycle_state = $LIFECYCLE_STATE,
    bva.boot_volume_id = $BOOT_VOLUME_ID,
    bva.lastupdated = $oci_update_tag
    WITH bva
    MATCH (inode:OCIInstance{ocid: $INSTANCE_ID})
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
    MERGE (va:OCIVolumeAttachment{ocid: $OCID})
    ON CREATE SET va.firstseen = timestamp(),
    va.createdate = $TIME_CREATED
    SET va.display_name = $DISPLAY_NAME,
    va.compartment_id = $COMPARTMENT_ID,
    va.availability_domain = $AVAILABILITY_DOMAIN,
    va.lifecycle_state = $LIFECYCLE_STATE,
    va.volume_id = $VOLUME_ID,
    va.attachment_type = $ATTACHMENT_TYPE,
    va.is_read_only = $IS_READ_ONLY,
    va.lastupdated = $oci_update_tag
    WITH va
    MATCH (inode:OCIInstance{ocid: $INSTANCE_ID})
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
    logger.debug("Syncing OCI compute instances for tenancy '%s', region '%s'.", tenancy_id, region)
    for compartment in compartments:
        data = get_instance_list_data(compute, compartment["ocid"])
        if data["Instances"]:
            load_instances(neo4j_session, data["Instances"], tenancy_id, compartment["ocid"], region, oci_update_tag)


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
    logger.debug("Syncing OCI VNIC attachments for tenancy '%s'.", tenancy_id)
    for compartment in compartments:
        data = get_vnic_attachment_list_data(compute, compartment["ocid"])
        if data["VnicAttachments"]:
            load_vnic_attachments(neo4j_session, data["VnicAttachments"], tenancy_id, oci_update_tag)


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
    logger.debug("Syncing OCI images for tenancy '%s'.", tenancy_id)
    for compartment in compartments:
        data = get_image_list_data(compute, compartment["ocid"])
        if data["Images"]:
            load_images(neo4j_session, data["Images"], tenancy_id, compartment["ocid"], oci_update_tag)


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
    logger.debug("Syncing OCI volume attachments for tenancy '%s'.", tenancy_id)
    for compartment in compartments:
        data = get_volume_attachment_list_data(compute, compartment["ocid"])
        if data["VolumeAttachments"]:
            load_volume_attachments(neo4j_session, data["VolumeAttachments"], tenancy_id, oci_update_tag)


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
    compartment_ocid = common_job_parameters.get("OCI_COMPARTMENT_ID", tenancy_id)
    logger.info("Syncing OCI Compute for compartment '%s'.", compartment_ocid)

    # Use only the target compartment for resource listing
    compartments = [{"ocid": compartment_ocid, "name": "target", "compartmentid": tenancy_id}]

    # If no regions provided, use the compute client's current region
    if not regions:
        regions = [compute.base_client.region or ""]

    for region in regions:
        logger.info("Syncing OCI Compute in region '%s' for compartment '%s'.", region, compartment_ocid)
        compute.base_client.set_region(region)

        # Sync instances
        sync_instances(neo4j_session, compute, compartments, tenancy_id, region, oci_update_tag, common_job_parameters)

        # Sync VNIC attachments (links instances to network interfaces)
        sync_vnic_attachments(neo4j_session, compute, compartments, tenancy_id, oci_update_tag, common_job_parameters)

        # Sync images
        sync_images(neo4j_session, compute, compartments, tenancy_id, oci_update_tag, common_job_parameters)

        # Sync volume attachments (block volumes attached to instances)
        sync_volume_attachments(neo4j_session, compute, compartments, tenancy_id, oci_update_tag, common_job_parameters)

    # Cleanup stale nodes
    run_cleanup_job('oci_import_compute_instances_cleanup.json', neo4j_session, common_job_parameters)
