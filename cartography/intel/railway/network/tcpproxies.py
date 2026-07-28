import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.railway.serviceinstances import iter_service_instances
from cartography.intel.railway.utils import build_tcp_proxy_batch_query
from cartography.intel.railway.utils import call_railway_api
from cartography.intel.railway.utils import is_live_entrypoint
from cartography.models.railway.network.tcpproxy import RailwayTCPProxySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# `tcpProxies` is a root field keyed by (serviceId, environmentId), so a workspace with N
# services across M environments would cost N*M requests. Aliasing many lookups into one
# document keeps that within Railway's hourly budget.
_ALIASES_PER_REQUEST = 50


@timeit
def get_all(
    api_session: requests.Session,
    base_url: str,
    bundles: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    """
    Fetch TCP proxies for every service instance in the given project bundles.

    Fetching is split from loading because of a circular ordering constraint: service
    instances need the proxies to decide `is_publicly_exposed`, while the proxies' EXPOSE
    edges need the service instance nodes to already exist.

    :return: (project id -> its proxies, service instance id -> its proxies)
    """
    by_project: dict[str, list[dict[str, Any]]] = {}
    by_instance: dict[str, list[dict[str, Any]]] = {}
    for project_id, bundle in bundles.items():
        proxies_by_instance = get(
            api_session,
            base_url,
            iter_service_instances(bundle),
        )
        by_instance.update(proxies_by_instance)
        by_project[project_id] = [
            proxy for proxies in proxies_by_instance.values() for proxy in proxies
        ]
    return by_project, by_instance


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    """
    Load the TCP proxies already fetched by get_all(). Must run after the service instance
    sync so the EXPOSE edges resolve.
    """
    load_tcp_proxies(neo4j_session, by_project, update_tag)
    cleanup(neo4j_session, list(by_project), common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    instances: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Fetch TCP proxies for a batch of service instances, denormalising the owning
    (service, environment) pair back onto each proxy.
    """
    results: dict[str, list[dict[str, Any]]] = {}

    for start in range(0, len(instances), _ALIASES_PER_REQUEST):
        chunk = instances[start : start + _ALIASES_PER_REQUEST]
        pairs = [
            (instance["serviceId"], instance["environmentId"]) for instance in chunk
        ]
        data = call_railway_api(
            api_session,
            base_url,
            build_tcp_proxy_batch_query(pairs),
        )
        # Aliases are positional (p0, p1, ...), so the response maps back onto `chunk` by
        # index. That is the only link between a proxy and the instance that owns it.
        for index, instance in enumerate(chunk):
            proxies = data.get(f"p{index}") or []
            results[instance["id"]] = [
                {
                    **proxy,
                    "service_id": instance["serviceId"],
                    "environment_id": instance["environmentId"],
                    # Null unless the proxy is actually serving, so a CREATING or DELETING
                    # proxy gets no EXPOSE edge. Mirrors the domain transforms and the
                    # is_publicly_exposed flag.
                    "exposed_service_id": (
                        instance["serviceId"] if is_live_entrypoint(proxy) else None
                    ),
                    "exposed_environment_id": (
                        instance["environmentId"] if is_live_entrypoint(proxy) else None
                    ),
                }
                for proxy in proxies
            ]

    return results


@timeit
def load_tcp_proxies(
    neo4j_session: neo4j.Session,
    by_project: dict[str, list[dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, proxies in by_project.items():
        load(
            neo4j_session,
            RailwayTCPProxySchema(),
            proxies,
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
            RailwayTCPProxySchema(),
            scoped_job_parameters,
        ).run(neo4j_session)
