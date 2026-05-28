import json
import logging
from typing import Any

import neo4j

from cartography.util import run_scoped_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _normalize_ts_net_hostname(hostname: str | None) -> tuple[str, str, str] | None:
    if not hostname:
        return None

    normalized = hostname.lower().rstrip(".")
    if not normalized.endswith(".ts.net"):
        return None

    parts = normalized.split(".", maxsplit=1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None

    return normalized, parts[0], parts[1]


def _extract_service_load_balancer_ingress_hostnames(
    load_balancer_ingress: str | None,
) -> list[str]:
    if not load_balancer_ingress:
        return []

    try:
        ingress_entries = json.loads(load_balancer_ingress)
    except json.JSONDecodeError:
        logger.debug("Unable to parse KubernetesService.load_balancer_ingress JSON")
        return []

    if not isinstance(ingress_entries, list):
        return []

    hostnames = []
    for entry in ingress_entries:
        if not isinstance(entry, dict):
            continue
        hostname = entry.get("hostname")
        if isinstance(hostname, str):
            hostnames.append(hostname)
    return hostnames


def _append_endpoint_candidate(
    candidates: list[dict[str, str]],
    seen: set[tuple[str, str, str]],
    resource_type: str,
    resource_id: str,
    hostname: str | None,
    source_field: str,
) -> None:
    normalized = _normalize_ts_net_hostname(hostname)
    if not normalized:
        return

    host, short_name, tailnet_suffix = normalized
    candidate_key = (resource_type, resource_id, host)
    if candidate_key in seen:
        return

    seen.add(candidate_key)
    candidates.append(
        {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "host": host,
            "short_name": short_name,
            "tailnet_suffix": tailnet_suffix,
            "source_field": source_field,
        },
    )


def build_endpoint_candidates(
    rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for row in rows:
        resource_type = row["resource_type"]
        resource_id = row["resource_id"]

        for hostname in row.get("host_names") or []:
            _append_endpoint_candidate(
                candidates,
                seen,
                resource_type,
                resource_id,
                hostname,
                "ingress.host_names",
            )

        for hostname in row.get("load_balancer_dns_names") or []:
            source_field = (
                "ingress.load_balancer_dns_names"
                if resource_type == "ingress"
                else "service.load_balancer_dns_names"
            )
            _append_endpoint_candidate(
                candidates,
                seen,
                resource_type,
                resource_id,
                hostname,
                source_field,
            )

        if resource_type == "service":
            for hostname in _extract_service_load_balancer_ingress_hostnames(
                row.get("load_balancer_ingress"),
            ):
                _append_endpoint_candidate(
                    candidates,
                    seen,
                    resource_type,
                    resource_id,
                    hostname,
                    "service.load_balancer_ingress.hostname",
                )

    return candidates


def get_kubernetes_endpoint_rows(
    neo4j_session: neo4j.Session,
    cluster_id: str,
) -> list[dict[str, Any]]:
    result = neo4j_session.run(
        """
        MATCH (:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(ing:KubernetesIngress)
        RETURN 'ingress' AS resource_type,
               ing.id AS resource_id,
               ing.host_names AS host_names,
               ing.load_balancer_dns_names AS load_balancer_dns_names,
               null AS load_balancer_ingress
        UNION ALL
        MATCH (:KubernetesCluster{id: $CLUSTER_ID})-[:RESOURCE]->(svc:KubernetesService)
        RETURN 'service' AS resource_type,
               svc.id AS resource_id,
               [] AS host_names,
               svc.load_balancer_dns_names AS load_balancer_dns_names,
               svc.load_balancer_ingress AS load_balancer_ingress
        """,
        CLUSTER_ID=cluster_id,
    )
    return [dict(record) for record in result]


@timeit
def run_tailscale_endpoint_linking(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    endpoint_rows = get_kubernetes_endpoint_rows(
        neo4j_session,
        common_job_parameters["CLUSTER_ID"],
    )
    job_parameters = common_job_parameters.copy()
    job_parameters["K8S_TAILSCALE_ENDPOINTS"] = build_endpoint_candidates(endpoint_rows)

    run_scoped_analysis_job(
        "k8s_tailscale_endpoint_linking.json",
        neo4j_session,
        job_parameters,
    )
