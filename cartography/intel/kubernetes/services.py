import json
import logging
from typing import Any

import neo4j
from kubernetes.client.models import V1LoadBalancerIngress
from kubernetes.client.models import V1PortStatus
from kubernetes.client.models import V1Service

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.services import KubernetesServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_services(client: K8sClient) -> list[V1Service]:
    items = k8s_paginate(client.core.list_service_for_all_namespaces)
    return items


def _format_service_selector(selector: dict[str, str]) -> str:
    return json.dumps(selector)


def _format_load_balancer_ingress(ingress: list[V1LoadBalancerIngress] | None) -> str:

    def _format_ingress_ports(
        ports: list[V1PortStatus] | None,
    ) -> list[dict[str, Any]] | None:
        if ports is None:
            return None

        ingress_ports = []
        for port in ports:
            ingress_ports.append(
                {
                    "error": port.port,
                    "port": port.protocol,
                    "protocol": port.ip,
                }
            )
        return ingress_ports

    if ingress is None:
        return json.dumps(None)

    loadbalancer_ingress = []
    for item in ingress:
        loadbalancer_ingress.append(
            {
                "hostname": item.hostname,
                "ip": item.ip,
                "ip_mode": item.ip_mode,
                "ports": _format_ingress_ports(item.ports),
            }
        )
    return json.dumps(loadbalancer_ingress)


def transform_services(
    services: list[V1Service], all_pods: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    services_list = []
    for service in services:
        item = {
            "uid": service.metadata.uid,
            "name": service.metadata.name,
            "creation_timestamp": get_epoch(service.metadata.creation_timestamp),
            "deletion_timestamp": get_epoch(service.metadata.deletion_timestamp),
            "namespace": service.metadata.namespace,
            "type": service.spec.type,
            "selector": _format_service_selector(service.spec.selector),
            "cluster_ip": service.spec.cluster_ip,
            "load_balancer_ip": service.spec.load_balancer_ip,
        }

        # TODO: instead of storing a json string, we should probably create seperate nodes for each ingress
        if service.spec.type == "LoadBalancer":
            if service.status.load_balancer:
                item["load_balancer_ingress"] = _format_load_balancer_ingress(
                    service.status.load_balancer.ingress
                )

        # check if pod labels match service selector and add pod_ids to item
        pod_ids = []
        for pod in all_pods:
            if pod["namespace"] == service.metadata.namespace:
                service_selector: dict[str, str] | None = service.spec.selector
                pod_labels: dict[str, str] | None = json.loads(pod["labels"])

                # check if pod labels match service selector
                if pod_labels and service_selector:
                    if all(
                        service_selector[key] == pod_labels.get(key)
                        for key in service_selector
                    ):
                        pod_ids.append(pod["uid"])

        item["pod_ids"] = pod_ids

        services_list.append(item)
    return services_list


def load_services(
    session: neo4j.Session,
    services: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(services)} KubernetesServices")
    load(
        session,
        KubernetesServiceSchema(),
        services,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup job for KubernetesService")
    cleanup_job = GraphJob.from_node_schema(
        KubernetesServiceSchema(), common_job_parameters
    )
    cleanup_job.run(session)


@timeit
def sync_services(
    session: neo4j.Session,
    client: K8sClient,
    all_pods: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    services = get_services(client)
    transformed_services = transform_services(services, all_pods)
    load_services(
        session=session,
        services=transformed_services,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    cleanup(session, common_job_parameters)
