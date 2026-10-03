import json
import logging
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1EndpointSlice
from urllib3.exceptions import HTTPError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import get_qualified_resource_name
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.endpoint_slices import KubernetesEndpointSliceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

SERVICE_NAME_LABEL = "kubernetes.io/service-name"
MANAGED_BY_LABEL = "endpointslice.kubernetes.io/managed-by"


@timeit
def get_endpoint_slices(client: K8sClient) -> list[V1EndpointSlice]:
    return k8s_paginate(
        client.discovery.list_endpoint_slice_for_all_namespaces,
        raise_on_error=True,
    )


def transform_endpoint_slices(
    endpoint_slices: list[V1EndpointSlice],
) -> list[dict[str, Any]]:
    transformed = []
    for endpoint_slice in endpoint_slices:
        metadata = endpoint_slice.metadata
        labels = metadata.labels or {}
        namespace = metadata.namespace
        service_name = labels.get(SERVICE_NAME_LABEL)
        endpoints = []
        ready_pod_ids = set()
        for endpoint in endpoint_slice.endpoints or []:
            target_ref = endpoint.target_ref
            ready = (
                endpoint.conditions is None or endpoint.conditions.ready is not False
            )
            if ready and target_ref and target_ref.kind == "Pod" and target_ref.uid:
                ready_pod_ids.add(target_ref.uid)
            endpoints.append(
                {
                    "addresses": endpoint.addresses,
                    "hostname": endpoint.hostname,
                    "node_name": endpoint.node_name,
                    "zone": endpoint.zone,
                    "ready": (
                        endpoint.conditions.ready if endpoint.conditions else None
                    ),
                    "serving": (
                        endpoint.conditions.serving if endpoint.conditions else None
                    ),
                    "terminating": (
                        endpoint.conditions.terminating if endpoint.conditions else None
                    ),
                    "target_ref": (
                        {
                            "api_version": target_ref.api_version,
                            "kind": target_ref.kind,
                            "name": target_ref.name,
                            "namespace": target_ref.namespace,
                            "uid": target_ref.uid,
                        }
                        if target_ref
                        else None
                    ),
                }
            )

        ports = [
            {
                "name": port.name,
                "port": port.port,
                "protocol": port.protocol or "TCP",
                "app_protocol": port.app_protocol,
            }
            for port in endpoint_slice.ports or []
        ]
        transformed.append(
            {
                "uid": metadata.uid,
                "name": metadata.name,
                "namespace": namespace,
                "address_type": endpoint_slice.address_type,
                "managed_by": labels.get(MANAGED_BY_LABEL),
                "service_qualified_name": (
                    get_qualified_resource_name(namespace, service_name)
                    if namespace and service_name
                    else None
                ),
                "endpoints": json.dumps(endpoints, sort_keys=True),
                "ports": json.dumps(ports, sort_keys=True),
                "port_numbers": sorted(
                    {port["port"] for port in ports if port["port"] is not None}
                ),
                "ready_pod_ids": sorted(ready_pod_ids),
                "creation_timestamp": get_epoch(metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(metadata.deletion_timestamp),
            }
        )
    return transformed


def service_pod_ids_by_qualified_name(
    endpoint_slices: list[dict[str, Any]],
) -> dict[str, list[str]]:
    service_pod_ids: dict[str, set[str]] = {}
    for endpoint_slice in endpoint_slices:
        service_qualified_name = endpoint_slice["service_qualified_name"]
        if not service_qualified_name:
            continue
        service_pod_ids.setdefault(service_qualified_name, set()).update(
            endpoint_slice["ready_pod_ids"]
        )
    return {service: sorted(pod_ids) for service, pod_ids in service_pod_ids.items()}


def load_endpoint_slices(
    session: neo4j.Session,
    endpoint_slices: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        session,
        KubernetesEndpointSliceSchema(),
        endpoint_slices,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    GraphJob.from_node_schema(
        KubernetesEndpointSliceSchema(), common_job_parameters
    ).run(session)


def get_endpoint_slice_data(
    client: K8sClient,
) -> list[dict[str, Any]] | None:
    try:
        endpoint_slices = transform_endpoint_slices(get_endpoint_slices(client))
    except ApiException as error:
        if error.status == 404:
            logger.info(
                "The discovery.k8s.io/v1 EndpointSlice API is unavailable on "
                "cluster %s. Falling back to selector-based Service backends and "
                "preserving previously synced EndpointSlice nodes.",
                client.name,
            )
            return None
        if error.status in (401, 403):
            logger.warning(
                "Cartography lacks permission to list EndpointSlices on cluster "
                "%s (status %s). Falling back to selector-based Service backends "
                "and preserving previously synced EndpointSlice nodes. Grant list "
                "on endpointslices.discovery.k8s.io; this permission will be "
                "required in v1.0.0.",
                client.name,
                error.status,
            )
            return None
        status = error.status or 0
        if status in (0, 429) or 500 <= status < 600:
            logger.error(
                "Transient Kubernetes API error listing EndpointSlices on cluster "
                "%s (status %s). Falling back to selector-based Service backends "
                "and preserving previously synced EndpointSlice nodes.",
                client.name,
                error.status,
            )
            return None
        raise
    except HTTPError:
        logger.exception(
            "Kubernetes transport error listing EndpointSlices on cluster %s. "
            "Falling back to selector-based Service backends and preserving "
            "previously synced EndpointSlice nodes.",
            client.name,
        )
        return None

    return endpoint_slices


@timeit
def sync_endpoint_slices(
    session: neo4j.Session,
    endpoint_slices: list[dict[str, Any]],
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    load_endpoint_slices(
        session,
        endpoint_slices,
        update_tag,
        common_job_parameters["CLUSTER_ID"],
        client.name,
    )
    cleanup(session, common_job_parameters)
