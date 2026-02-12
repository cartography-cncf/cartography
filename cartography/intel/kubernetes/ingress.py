import json
import logging
from typing import Any

import neo4j
from kubernetes.client.models import V1HTTPIngressRuleValue
from kubernetes.client.models import V1Ingress
from kubernetes.client.models import V1IngressBackend
from kubernetes.client.models import V1IngressLoadBalancerIngress
from kubernetes.client.models import V1IngressRule

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.ingress import KubernetesIngressSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_ingress(client: K8sClient) -> list[V1Ingress]:
    items = k8s_paginate(client.networking.list_ingress_for_all_namespaces)
    return items


def _format_ingress_backend(backend: V1IngressBackend | None) -> dict[str, Any]:
    transformed_backend: dict[str, Any] = {}

    if backend is None:
        return transformed_backend

    if backend.resource:
        transformed_backend["backend_resource_name"] = backend.resource.name
    if backend.service:
        transformed_backend["backend_service_name"] = backend.service.name
        if backend.service.port:
            transformed_backend["backend_service_port_name"] = backend.service.port.name
            transformed_backend["backend_service_port_number"] = (
                backend.service.port.number
            )
    return transformed_backend


def _format_ingress_rules(rules: list[V1IngressRule] | None) -> list[dict[str, Any]]:

    def _format_ingress_rule_paths(
        http: V1HTTPIngressRuleValue | None,
    ) -> list[dict[str, Any]] | None:
        if http is None:
            return None

        paths = http.paths or []
        transformed_paths = []

        # incoming requests matching a path are routed to the backend service
        for path in paths:
            transformed_path = {
                "path": path.path,
                "path_type": path.path_type,
            }
            transformed_backend = _format_ingress_backend(path.backend)
            transformed_path = transformed_path | transformed_backend
            transformed_paths.append(transformed_path)

        return transformed_paths

    transformed_rules: list[dict[str, Any]] = []
    if rules is None:
        return transformed_rules

    # an ingress rule maps the paths under a specified
    # host to a backend service. host names are optional.
    for rule in rules:
        transformed_rules.append(
            {
                "host": rule.host,  # will be None when host is not specified
                "paths": _format_ingress_rule_paths(rule.http),
            }
        )
    return transformed_rules


def _extract_load_balancer_dns_names(
    ingress_status: list[V1IngressLoadBalancerIngress] | None,
) -> list[str]:
    """
    Extract DNS hostnames from ingress load balancer status.
    Used to match KubernetesIngress to cloud load balancer nodes.
    """
    if ingress_status is None:
        return []

    dns_names = []
    for item in ingress_status:
        if item.hostname:
            dns_names.append(item.hostname)
    return dns_names


def transform_ingresses(ingress: list[V1Ingress]) -> list[dict[str, Any]]:
    transformed_ingresses: list[dict[str, Any]] = []

    for item in ingress:
        transformed_rules = _format_ingress_rules(item.spec.rules)

        backend_services = set()
        # extract backend services from ingress rules
        for rule in transformed_rules:
            for path in rule.get("paths") or []:
                if path.get("backend_service_name"):
                    backend_services.add(path["backend_service_name"])

        # include default backend service if specified
        if item.spec.default_backend:
            default_backend_service = _format_ingress_backend(item.spec.default_backend)
            if default_backend_service.get("backend_service_name"):
                backend_services.add(default_backend_service["backend_service_name"])

        # extract load balancer DNS names from status for cloud LB matching
        load_balancer_dns_names: list[str] = []
        if item.status and item.status.load_balancer:
            load_balancer_dns_names = _extract_load_balancer_dns_names(
                item.status.load_balancer.ingress
            )

        # extract ingress group name from annotations (used in AWS Load Balancer Controller)
        annotations = item.metadata.annotations or {}
        ingress_group_name = annotations.get("alb.ingress.kubernetes.io/group.name")

        transformed_ingresses.append(
            {
                "uid": item.metadata.uid,
                "name": item.metadata.name,
                "namespace": item.metadata.namespace,
                "creation_timestamp": get_epoch(item.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(item.metadata.deletion_timestamp),
                "annotations": json.dumps(item.metadata.annotations),
                "ingress_class_name": item.spec.ingress_class_name,
                "rules": json.dumps(_format_ingress_rules(item.spec.rules)),
                "default_backend": json.dumps(
                    _format_ingress_backend(item.spec.default_backend)
                ),
                "target_services": list(backend_services),
                "ingress_group_name": ingress_group_name,
                "load_balancer_dns_names": load_balancer_dns_names,
            }
        )
    return transformed_ingresses


def load_ingresses(
    neo4j_session: neo4j.Session,
    ingresses: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        neo4j_session,
        KubernetesIngressSchema(),
        ingresses,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup job for KubernetesIngress")
    cleanup_job = GraphJob.from_node_schema(
        KubernetesIngressSchema(), common_job_parameters
    )
    cleanup_job.run(session)


@timeit
def sync_ingress(
    neo4j_session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info(f"Syncing ingress for cluster {client.name}")
    ingresses = get_ingress(client)
    transformed_ingresses = transform_ingresses(ingresses)
    load_ingresses(
        neo4j_session,
        transformed_ingresses,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    cleanup(neo4j_session, common_job_parameters)
