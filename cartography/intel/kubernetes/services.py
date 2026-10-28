import json
import logging
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1LoadBalancerIngress
from kubernetes.client.models import V1PortStatus
from kubernetes.client.models import V1Service

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import gcp_forwarding_rule_match_keys
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import get_gke_network_scope
from cartography.intel.kubernetes.util import get_qualified_resource_name
from cartography.intel.kubernetes.util import GKENetworkScope
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.services import KubernetesServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GKE_NEG_STATUS_ANNOTATION = "cloud.google.com/neg-status"


@timeit
def get_services(client: K8sClient) -> list[V1Service]:
    items = k8s_paginate(
        client.core.list_service_for_all_namespaces, raise_on_error=True
    )
    return items


def _format_service_selector(selector: dict[str, str]) -> str:
    return json.dumps(selector)


def _extract_load_balancer_dns_names(
    ingress: list[V1LoadBalancerIngress] | None,
) -> list[str]:
    """
    Extract DNS hostnames from load balancer ingress entries.
    These can be used to match Kubernetes Services to AWS LoadBalancerV2 nodes.

    Lowercased to match AWSLoadBalancerV2.dnsname, which is also lowercased at ingestion:
    the in-cluster controller copies the ELB DNSName verbatim, so it can be mixed case.
    """
    if ingress is None:
        return []

    dns_names = []
    for item in ingress:
        if item.hostname:
            dns_names.append(item.hostname.lower())
    return dns_names


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
                    "error": port.error,
                    "port": port.port,
                    "protocol": port.protocol,
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


def _gcp_neg_ids(
    annotations: dict[str, str] | None,
    gke_scope: GKENetworkScope | None,
) -> list[str]:
    """
    Build the partial URIs of the zonal NEGs GKE lists in `cloud.google.com/neg-status`.
    The annotation holds NEG names by service port and the zones they span; the
    project comes from the cluster, since NEGs always live in the cluster's project.
    """
    if gke_scope is None or not annotations:
        return []
    raw_status = annotations.get(GKE_NEG_STATUS_ANNOTATION)
    if not raw_status:
        return []
    try:
        status = json.loads(raw_status)
    except json.JSONDecodeError:
        logger.warning(
            "Ignoring unparseable %s annotation: %r",
            GKE_NEG_STATUS_ANNOTATION,
            raw_status,
        )
        return []
    neg_names = sorted(set((status.get("network_endpoint_groups") or {}).values()))
    return [
        f"projects/{gke_scope.project_id}/zones/{zone}/networkEndpointGroups/{name}"
        for zone in status.get("zones") or []
        for name in neg_names
    ]


def transform_services(
    services: list[V1Service],
    all_pods: list[dict[str, Any]],
    gke_scope: GKENetworkScope | None = None,
) -> list[dict[str, Any]]:
    services_list = []
    for service in services:
        item = {
            "uid": service.metadata.uid,
            "name": service.metadata.name,
            "creation_timestamp": get_epoch(service.metadata.creation_timestamp),
            "deletion_timestamp": get_epoch(service.metadata.deletion_timestamp),
            "namespace": service.metadata.namespace,
            "qualified_name": get_qualified_resource_name(
                service.metadata.namespace, service.metadata.name
            ),
            "type": service.spec.type,
            "selector": _format_service_selector(service.spec.selector),
            "cluster_ip": service.spec.cluster_ip,
            "load_balancer_ip": service.spec.load_balancer_ip,
            "load_balancer_ips": [],
        }

        # TODO: instead of storing a json string, we should probably create seperate nodes for each ingress
        if service.spec.type == "LoadBalancer":
            if service.status and service.status.load_balancer:
                item["load_balancer_ips"] = sorted(
                    {i.ip for i in service.status.load_balancer.ingress or [] if i.ip}
                )
                item["load_balancer_ingress"] = _format_load_balancer_ingress(
                    service.status.load_balancer.ingress
                )
                # Extract DNS names for relationship matching with AWS LoadBalancerV2
                item["load_balancer_dns_names"] = _extract_load_balancer_dns_names(
                    service.status.load_balancer.ingress
                )
        item.update(
            gcp_forwarding_rule_match_keys(item["load_balancer_ips"], gke_scope)
        )
        item["gcp_neg_ids"] = _gcp_neg_ids(service.metadata.annotations, gke_scope)

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
    try:
        services = get_services(client)
    except ApiException as err:
        if err.status in (401, 403):
            # A partial services snapshot cannot be told apart from an empty one, so skip
            # load + cleanup and keep the previous data, like `sync_secrets`.
            logger.warning(
                "Cartography lacks permission to list services on cluster %s (status %s). "
                "Skipping services sync and preserving previously synced data.",
                client.name,
                err.status,
            )
            return
        raise
    transformed_services = transform_services(
        services, all_pods, get_gke_network_scope(client)
    )
    load_services(
        session=session,
        services=transformed_services,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    cleanup(session, common_job_parameters)
