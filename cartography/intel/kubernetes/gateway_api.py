import logging
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import get_qualified_resource_name
from cartography.intel.kubernetes.util import K8sClient
from cartography.intel.kubernetes.util import parse_rfc3339
from cartography.models.kubernetes.gateway_api import KubernetesGatewaySchema
from cartography.models.kubernetes.gateway_api import KubernetesHTTPRouteSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

GATEWAY_API_GROUP = "gateway.networking.k8s.io"
CORE_API_GROUP = ""
GATEWAY_KIND = "Gateway"
SERVICE_KIND = "Service"


def _ref_matches(
    ref: dict[str, Any],
    *,
    default_group: str,
    default_kind: str,
    group: str,
    kind: str,
) -> bool:
    # Per the Gateway API spec, an empty/missing `group` means the core API group
    # (`""`) and an empty/missing `kind` means `Service` for backendRefs and
    # `Gateway` for parentRefs. `or` correctly treats both `None` and `""` as
    # "use the default".
    return (ref.get("group") or default_group) == group and (
        ref.get("kind") or default_kind
    ) == kind


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

        try:
            response = client.custom.list_cluster_custom_object(
                group=group,
                version=version,
                plural=plural,
                limit=100,
                **kwargs,
            )
        except ApiException as err:
            if err.status == 404:
                logger.info(
                    "Skipping %s for cluster %s because the CRD is not installed.",
                    resource_name,
                    client.name,
                )
                return []

            logger.warning(
                "Failed to fetch %s resources for cluster %s: %s",
                resource_name,
                client.name,
                err,
            )
            raise

        items = response.get("items", [])
        all_resources.extend(items)

        continue_token = response.get("metadata", {}).get("continue")
        if not continue_token:
            break

    logger.debug("Fetched %d %s resources", len(all_resources), resource_name)
    return all_resources


@timeit
def get_gateways(client: K8sClient) -> list[dict[str, Any]]:
    return _list_cluster_custom_objects(
        client,
        group=GATEWAY_API_GROUP,
        version="v1",
        plural="gateways",
    )


@timeit
def get_http_routes(client: K8sClient) -> list[dict[str, Any]]:
    return _list_cluster_custom_objects(
        client,
        group=GATEWAY_API_GROUP,
        version="v1",
        plural="httproutes",
    )


def transform_gateways(gateways: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []

    for gateway in gateways:
        metadata = gateway.get("metadata", {})
        spec = gateway.get("spec", {})
        namespace = metadata["namespace"]
        name = metadata["name"]

        transformed.append(
            {
                "uid": metadata["uid"],
                "name": name,
                "namespace": namespace,
                "qualified_name": get_qualified_resource_name(namespace, name),
                "gateway_class_name": spec.get("gatewayClassName"),
                "creation_timestamp": get_epoch(
                    parse_rfc3339(metadata.get("creationTimestamp"))
                ),
                "deletion_timestamp": get_epoch(
                    parse_rfc3339(metadata.get("deletionTimestamp"))
                ),
                "attached_route_qualified_names": [],
            }
        )

    return transformed


def transform_http_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []

    for route in routes:
        metadata = route.get("metadata", {})
        spec = route.get("spec", {})
        namespace = metadata["namespace"]
        name = metadata["name"]

        backend_pairs: set[tuple[str, str]] = set()
        for rule in spec.get("rules") or []:
            for backend in rule.get("backendRefs") or []:
                if not _ref_matches(
                    backend,
                    default_group=CORE_API_GROUP,
                    default_kind=SERVICE_KIND,
                    group=CORE_API_GROUP,
                    kind=SERVICE_KIND,
                ):
                    continue

                backend_name = backend.get("name")
                if not backend_name:
                    continue
                backend_namespace = backend.get("namespace") or namespace
                if backend_namespace:
                    backend_pairs.add((backend_namespace, backend_name))

        parent_gateway_qualified_names: set[str] = set()
        for parent_ref in spec.get("parentRefs") or []:
            if not _ref_matches(
                parent_ref,
                default_group=GATEWAY_API_GROUP,
                default_kind=GATEWAY_KIND,
                group=GATEWAY_API_GROUP,
                kind=GATEWAY_KIND,
            ):
                continue

            parent_name = parent_ref.get("name")
            if not parent_name:
                continue
            parent_namespace = parent_ref.get("namespace") or namespace
            if parent_namespace:
                parent_gateway_qualified_names.add(
                    get_qualified_resource_name(parent_namespace, parent_name)
                )

        transformed.append(
            {
                "uid": metadata["uid"],
                "name": name,
                "namespace": namespace,
                "qualified_name": get_qualified_resource_name(namespace, name),
                "hostnames": spec.get("hostnames") or [],
                "creation_timestamp": get_epoch(
                    parse_rfc3339(metadata.get("creationTimestamp"))
                ),
                "deletion_timestamp": get_epoch(
                    parse_rfc3339(metadata.get("deletionTimestamp"))
                ),
                "backend_service_qualified_names": [
                    get_qualified_resource_name(service_namespace, service_name)
                    for service_namespace, service_name in sorted(backend_pairs)
                ],
                "parent_gateway_qualified_names": sorted(
                    parent_gateway_qualified_names
                ),
            }
        )

    return transformed


def _enrich_gateways_with_attached_routes(
    gateways: list[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> None:
    route_parents: dict[str, set[str]] = {}
    for route in routes:
        route_qualified_name = route["qualified_name"]
        for gateway_qualified_name in route.get("parent_gateway_qualified_names", []):
            route_parents.setdefault(gateway_qualified_name, set()).add(
                route_qualified_name
            )

    for gateway in gateways:
        gateway["attached_route_qualified_names"] = sorted(
            route_parents.get(gateway["qualified_name"], set())
        )


@timeit
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


@timeit
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


@timeit
def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup job for Kubernetes gateway-api resources")
    GraphJob.from_node_schema(KubernetesHTTPRouteSchema(), common_job_parameters).run(
        session
    )
    GraphJob.from_node_schema(KubernetesGatewaySchema(), common_job_parameters).run(
        session
    )


@timeit
def sync_gateway_api(
    neo4j_session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    try:
        raw_gateways = get_gateways(client)
        raw_routes = get_http_routes(client)
    except ApiException as err:
        if err.status in (401, 403):
            # Skipping load + cleanup is intentional: if the operator previously
            # granted these verbs and later revoked them, running cleanup would
            # wipe the existing KubernetesGateway / KubernetesHTTPRoute subgraph
            # for this cluster. This mirrors the pattern in `sync_secrets`.
            logger.warning(
                "Cartography lacks permission to list gateways/httproutes on "
                "cluster %s (status %s). Skipping gateway-api sync and "
                "preserving previously synced data. Grant `list gateways` and "
                "`list httproutes` in the gateway.networking.k8s.io group to "
                "enable ingestion.",
                client.name,
                err.status,
            )
            return
        raise

    gateways = transform_gateways(raw_gateways)
    routes = transform_http_routes(raw_routes)
    _enrich_gateways_with_attached_routes(gateways, routes)

    # Load HTTPRoutes before Gateways: the Gateway -> HTTPRoute :ROUTES rel is
    # matched by `qualified_name` via `one_to_many`, so the HTTPRoute nodes must
    # already exist when Gateway is loaded.
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
