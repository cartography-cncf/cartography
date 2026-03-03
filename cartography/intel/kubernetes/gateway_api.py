import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.gateway_api import KubernetesGatewaySchema
from cartography.models.kubernetes.gateway_api import KubernetesHTTPRouteSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _list_cluster_custom_objects(
    client: K8sClient,
    group: str,
    version: str,
    plural: str,
) -> list[dict[str, Any]]:
    resource_name = f"{group}/{version}/{plural}"
    all_resources: list[dict[str, Any]] = []
    continue_token: str | None = None

    while True:
        kwargs: dict[str, Any] = {}
        if continue_token:
            kwargs["_continue"] = continue_token

        response = client.custom.list_cluster_custom_object(
            group=group,
            version=version,
            plural=plural,
            limit=100,
            **kwargs,
        )

        items = response.get("items", [])
        all_resources.extend(items)

        continue_token = response.get("metadata", {}).get("continue")
        if not continue_token:
            break

    logger.debug("Fetched %d %s resources", len(all_resources), resource_name)
    return all_resources


def get_gateways(client: K8sClient) -> list[dict[str, Any]]:
    return _list_cluster_custom_objects(
        client,
        group="gateway.networking.k8s.io",
        version="v1",
        plural="gateways",
    )


def get_http_routes(client: K8sClient) -> list[dict[str, Any]]:
    return _list_cluster_custom_objects(
        client,
        group="gateway.networking.k8s.io",
        version="v1",
        plural="httproutes",
    )


def transform_gateways(gateways: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []

    for gateway in gateways:
        metadata = gateway.get("metadata", {})
        spec = gateway.get("spec", {})

        transformed.append(
            {
                "uid": metadata.get("uid"),
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace"),
                "gateway_class_name": spec.get("gatewayClassName"),
                "creation_timestamp": get_epoch(metadata.get("creationTimestamp")),
                "deletion_timestamp": get_epoch(metadata.get("deletionTimestamp")),
                "attached_route_names": [],
                "attached_route_namespaces": [],
            }
        )

    return transformed


def transform_http_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []

    for route in routes:
        metadata = route.get("metadata", {})
        spec = route.get("spec", {})

        backend_pairs: set[tuple[str, str]] = set()
        for rule in spec.get("rules") or []:
            for backend in rule.get("backendRefs") or []:
                backend_name = backend.get("name")
                if not backend_name:
                    continue
                backend_namespace = backend.get("namespace") or metadata.get(
                    "namespace"
                )
                if backend_namespace:
                    backend_pairs.add((backend_namespace, backend_name))

        parent_pairs: set[tuple[str, str]] = set()
        for parent_ref in spec.get("parentRefs") or []:
            parent_name = parent_ref.get("name")
            if not parent_name:
                continue
            parent_namespace = parent_ref.get("namespace") or metadata.get("namespace")
            if parent_namespace:
                parent_pairs.add((parent_namespace, parent_name))

        transformed.append(
            {
                "uid": metadata.get("uid"),
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace"),
                "hostnames": spec.get("hostnames") or [],
                "creation_timestamp": get_epoch(metadata.get("creationTimestamp")),
                "deletion_timestamp": get_epoch(metadata.get("deletionTimestamp")),
                "backend_service_names": [name for _, name in sorted(backend_pairs)],
                "backend_service_namespaces": [
                    namespace for namespace, _ in sorted(backend_pairs)
                ],
                "parent_gateway_names": [name for _, name in sorted(parent_pairs)],
                "parent_gateway_namespaces": [
                    namespace for namespace, _ in sorted(parent_pairs)
                ],
            }
        )

    return transformed


def _enrich_gateways_with_attached_routes(
    gateways: list[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> None:
    route_parents: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for route in routes:
        route_namespace = route["namespace"]
        route_name = route["name"]
        for gateway_namespace, gateway_name in zip(
            route.get("parent_gateway_namespaces", []),
            route.get("parent_gateway_names", []),
            strict=False,
        ):
            route_parents.setdefault((gateway_namespace, gateway_name), set()).add(
                (route_namespace, route_name)
            )

    for gateway in gateways:
        attached = sorted(
            route_parents.get((gateway["namespace"], gateway["name"]), set())
        )
        gateway["attached_route_namespaces"] = [namespace for namespace, _ in attached]
        gateway["attached_route_names"] = [name for _, name in attached]


def load_gateways(
    neo4j_session: neo4j.Session,
    gateways: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        neo4j_session,
        KubernetesGatewaySchema(),
        gateways,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def load_http_routes(
    neo4j_session: neo4j.Session,
    routes: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        neo4j_session,
        KubernetesHTTPRouteSchema(),
        routes,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup job for Kubernetes gateway-api resources")
    GraphJob.from_node_schema(KubernetesGatewaySchema(), common_job_parameters).run(
        session
    )
    GraphJob.from_node_schema(KubernetesHTTPRouteSchema(), common_job_parameters).run(
        session
    )


@timeit
def sync_gateway_api(
    neo4j_session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    gateways = transform_gateways(get_gateways(client))
    routes = transform_http_routes(get_http_routes(client))
    _enrich_gateways_with_attached_routes(gateways, routes)

    load_http_routes(
        neo4j_session,
        routes,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    load_gateways(
        neo4j_session,
        gateways,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    cleanup(neo4j_session, common_job_parameters)
