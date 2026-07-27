import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.utils import unwrap_edges
from cartography.models.railway.serviceinstance import RailwayServiceInstanceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    bundles: dict[str, dict[str, Any]],
    tcp_proxies_by_instance: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    """
    Load the per-environment service instances from the already-fetched project bundles.

    :param tcp_proxies_by_instance: service instance id -> its TCP proxies. Needed to decide
        `is_publicly_exposed`, since tcpProxies is a separate root field rather than part of
        the bundle.
    """
    by_project = transform(bundles, tcp_proxies_by_instance)
    load_service_instances(neo4j_session, by_project, update_tag)
    cleanup(neo4j_session, list(bundles), common_job_parameters)


def iter_service_instances(
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Flatten every service instance across every environment of one project bundle.
    """
    instances = []
    for environment in unwrap_edges(bundle["environments"]):
        instances.extend(unwrap_edges(environment["serviceInstances"]))
    return instances


def _is_publicly_exposed(
    instance: dict[str, Any],
    tcp_proxies: list[dict[str, Any]],
) -> bool:
    domains = instance.get("domains") or {}
    if domains.get("serviceDomains"):
        # Railway-generated *.up.railway.app domains are always internet-facing.
        return True
    for custom_domain in domains.get("customDomains") or []:
        # An unverified custom domain does not resolve yet, so it is not yet exposure.
        if (custom_domain.get("status") or {}).get("verified"):
            return True
    return bool(tcp_proxies)


def transform(
    bundles: dict[str, dict[str, Any]],
    tcp_proxies_by_instance: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    by_project: dict[str, list[dict[str, Any]]] = {}
    for project_id, bundle in bundles.items():
        transformed = []
        for instance in iter_service_instances(bundle):
            source = instance.get("source") or {}
            latest_deployment = instance.get("latestDeployment") or {}
            tcp_proxies = tcp_proxies_by_instance.get(instance["id"], [])
            transformed.append(
                {
                    **instance,
                    "source_image": source.get("image"),
                    "source_repo": source.get("repo"),
                    "latest_deployment_id": latest_deployment.get("id"),
                    "latest_deployment_status": latest_deployment.get("status"),
                    "is_publicly_exposed": _is_publicly_exposed(instance, tcp_proxies),
                },
            )
        by_project[project_id] = transformed
    return by_project


@timeit
def load_service_instances(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, instances in by_project.items():
        load(
            neo4j_session,
            RailwayServiceInstanceSchema(),
            instances,
            lastupdated=update_tag,
            PROJECT_ID=project_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    project_ids: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    for project_id in project_ids:
        scoped_job_parameters = common_job_parameters.copy()
        scoped_job_parameters["PROJECT_ID"] = project_id
        GraphJob.from_node_schema(
            RailwayServiceInstanceSchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
