import json
import logging
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1PersistentVolume
from kubernetes.client.models import V1PersistentVolumeClaim
from kubernetes.client.models import V1StorageClass

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.storage import KubernetesPersistentVolumeClaimSchema
from cartography.models.kubernetes.storage import KubernetesPersistentVolumeSchema
from cartography.models.kubernetes.storage import KubernetesStorageClassSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_storage_classes(client: K8sClient) -> list[V1StorageClass]:
    return k8s_paginate(client.storage.list_storage_class, raise_on_error=True)


@timeit
def get_persistent_volumes(client: K8sClient) -> list[V1PersistentVolume]:
    return k8s_paginate(client.core.list_persistent_volume, raise_on_error=True)


@timeit
def get_persistent_volume_claims(client: K8sClient) -> list[V1PersistentVolumeClaim]:
    return k8s_paginate(
        client.core.list_persistent_volume_claim_for_all_namespaces,
        raise_on_error=True,
    )


def transform_storage_classes(
    storage_classes: list[V1StorageClass], cluster_name: str
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{cluster_name}/{storage_class.metadata.name}",
            "name": storage_class.metadata.name,
            "creation_timestamp": get_epoch(storage_class.metadata.creation_timestamp),
            "deletion_timestamp": get_epoch(storage_class.metadata.deletion_timestamp),
            "provisioner": storage_class.provisioner,
            "reclaim_policy": storage_class.reclaim_policy,
            "volume_binding_mode": storage_class.volume_binding_mode,
            "allow_volume_expansion": storage_class.allow_volume_expansion,
            "parameters": json.dumps(storage_class.parameters or {}, sort_keys=True),
            "mount_options": sorted(storage_class.mount_options or []),
        }
        for storage_class in storage_classes
    ]


def transform_persistent_volumes(
    volumes: list[V1PersistentVolume], cluster_name: str
) -> list[dict[str, Any]]:
    transformed = []
    for volume in volumes:
        spec = volume.spec
        status = volume.status
        claim_ref = getattr(spec, "claim_ref", None)
        csi = getattr(spec, "csi", None)
        storage_class_name = getattr(spec, "storage_class_name", None)
        transformed.append(
            {
                "id": f"{cluster_name}/{volume.metadata.name}",
                "uid": volume.metadata.uid,
                "name": volume.metadata.name,
                "creation_timestamp": get_epoch(volume.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(volume.metadata.deletion_timestamp),
                "capacity_storage": (spec.capacity or {}).get("storage"),
                "access_modes": sorted(spec.access_modes or []),
                "reclaim_policy": spec.persistent_volume_reclaim_policy,
                "storage_class_name": storage_class_name,
                "storage_class_id": (
                    f"{cluster_name}/{storage_class_name}"
                    if storage_class_name
                    else None
                ),
                "volume_mode": spec.volume_mode,
                "phase": getattr(status, "phase", None),
                "claim_namespace": getattr(claim_ref, "namespace", None),
                "claim_name": getattr(claim_ref, "name", None),
                "csi_driver": getattr(csi, "driver", None),
                "csi_volume_handle": getattr(csi, "volume_handle", None),
                "labels": json.dumps(volume.metadata.labels or {}, sort_keys=True),
            }
        )
    return transformed


def transform_persistent_volume_claims(
    claims: list[V1PersistentVolumeClaim], cluster_name: str
) -> list[dict[str, Any]]:
    transformed = []
    for claim in claims:
        spec = claim.spec
        status = claim.status
        namespace = claim.metadata.namespace
        storage_class_name = spec.storage_class_name
        volume_name = spec.volume_name
        requests = getattr(spec.resources, "requests", None) or {}
        transformed.append(
            {
                "id": f"{cluster_name}/{namespace}/{claim.metadata.name}",
                "uid": claim.metadata.uid,
                "name": claim.metadata.name,
                "creation_timestamp": get_epoch(claim.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(claim.metadata.deletion_timestamp),
                "namespace": namespace,
                "storage_class_name": storage_class_name,
                "storage_class_id": (
                    f"{cluster_name}/{storage_class_name}"
                    if storage_class_name
                    else None
                ),
                "volume_name": volume_name,
                "volume_id": (f"{cluster_name}/{volume_name}" if volume_name else None),
                "access_modes": sorted(spec.access_modes or []),
                "requested_storage": requests.get("storage"),
                "volume_mode": spec.volume_mode,
                "phase": getattr(status, "phase", None),
                "labels": json.dumps(claim.metadata.labels or {}, sort_keys=True),
            }
        )
    return transformed


@timeit
def load_storage(
    session: neo4j.Session,
    storage_classes: list[dict[str, Any]],
    volumes: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        session,
        KubernetesStorageClassSchema(),
        storage_classes,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )
    load(
        session,
        KubernetesPersistentVolumeSchema(),
        volumes,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )
    load(
        session,
        KubernetesPersistentVolumeClaimSchema(),
        claims,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    for schema in (
        KubernetesPersistentVolumeClaimSchema(),
        KubernetesPersistentVolumeSchema(),
        KubernetesStorageClassSchema(),
    ):
        logger.debug("Running cleanup job for %s", schema.label)
        GraphJob.from_node_schema(schema, common_job_parameters).run(session)


@timeit
def sync_storage(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    try:
        storage_classes = transform_storage_classes(
            get_storage_classes(client), client.name
        )
        volumes = transform_persistent_volumes(
            get_persistent_volumes(client), client.name
        )
        claims = transform_persistent_volume_claims(
            get_persistent_volume_claims(client), client.name
        )
    except ApiException as error:
        if error.status in (401, 403):
            # DEPRECATED: missing storage list permissions will become a hard
            # failure in v1.0.0. Preserve prior data during the migration window.
            logger.warning(
                "Cartography lacks permission to list persistent storage on "
                "cluster %s (status %s). Skipping storage sync and preserving "
                "previously synced StorageClass/PersistentVolume/"
                "PersistentVolumeClaim nodes. Grant list on storageclasses, "
                "persistentvolumes, and persistentvolumeclaims; these permissions "
                "will be required in v1.0.0.",
                client.name,
                error.status,
            )
            return
        raise

    load_storage(
        session,
        storage_classes,
        volumes,
        claims,
        update_tag,
        common_job_parameters["CLUSTER_ID"],
        client.name,
    )
    cleanup(session, common_job_parameters)
