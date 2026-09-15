import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.utils import is_live_entrypoint
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
    workspace: dict[str, Any],
    update_tag: int,
) -> None:
    """
    Load the per-environment service instances from the already-fetched project bundles.

    :param tcp_proxies_by_instance: service instance id -> its TCP proxies. Needed to decide
        `is_publicly_exposed`, since tcpProxies is a separate root field rather than part of
        the bundle.
    :param workspace: supplies preferredRegion, the effective region of any instance that
        does not override it.
    """
    by_project = transform(bundles, tcp_proxies_by_instance, workspace)
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


def _exposure_types(
    instance: dict[str, Any],
    tcp_proxies: list[dict[str, Any]],
) -> list[str]:
    """
    Which kinds of entry point are actually serving traffic right now.

    Merely having a domain or proxy object is not exposure: Railway keeps them around in
    CREATING, DELETING and DELETED states. is_live_entrypoint() also rejects a custom domain
    that has not passed DNS verification, since it does not resolve. This must stay in step
    with the EXPOSE edges, which are gated on the same predicate.

    A TCP proxy is reported separately from the HTTPS domains because it publishes a raw port
    with no TLS termination, which is a materially different exposure.
    """
    domains = instance.get("domains") or {}
    http_entrypoints = [
        *(domains.get("serviceDomains") or []),
        *(domains.get("customDomains") or []),
    ]
    types = []
    if any(is_live_entrypoint(entrypoint) for entrypoint in http_entrypoints):
        types.append("direct")
    if any(is_live_entrypoint(proxy) for proxy in tcp_proxies):
        types.append("tcp_proxy")
    return types


def transform(
    bundles: dict[str, dict[str, Any]],
    tcp_proxies_by_instance: dict[str, list[dict[str, Any]]],
    workspace: dict[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    # Railway only sets ServiceInstance.region when the instance overrides the workspace
    # default, which is rare, so most instances report null. Falling back to the workspace's
    # preferred region is what actually answers "where does this run", and it is what the
    # ComputeService ontology mapping reads. numReplicas scales an instance within that one
    # region: Railway exposes no per-replica placement, so there is nothing finer to model.
    default_region = (workspace or {}).get("preferredRegion")
    by_project: dict[str, list[dict[str, Any]]] = {}
    for project_id, bundle in bundles.items():
        transformed = []
        for instance in iter_service_instances(bundle):
            source = instance.get("source") or {}
            latest_deployment = instance.get("latestDeployment") or {}
            tcp_proxies = tcp_proxies_by_instance.get(instance["id"], [])
            exposure_types = _exposure_types(instance, tcp_proxies)
            transformed.append(
                {
                    **instance,
                    "source_image": source.get("image"),
                    "source_repo": source.get("repo"),
                    "latest_deployment_id": latest_deployment.get("id"),
                    "latest_deployment_status": latest_deployment.get("status"),
                    "region": instance.get("region") or default_region,
                    "region_is_workspace_default": not instance.get("region"),
                    "exposed_internet": bool(exposure_types),
                    "exposed_internet_type": exposure_types or None,
                    # DEPRECATED: kept in step with exposed_internet until v1.0.0.
                    "is_publicly_exposed": bool(exposure_types),
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
