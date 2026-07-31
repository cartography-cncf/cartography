import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.proxy import ModalProxyIPSchema
from cartography.models.modal.proxy import ModalProxySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
    all_proxies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ingest the proxies of one environment, with their egress IPs.

    `ProxyList` is workspace-wide and tags each proxy with its environment, so the caller
    fetches it once and this partitions it. Doing the fetch here would repeat the same request
    for every environment. The filter is deterministic and the listing complete, so the
    environment-scoped cleanup is safe.
    """
    environment_name = common_job_parameters["ENVIRONMENT_NAME"]
    environment_id = common_job_parameters["ENVIRONMENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    scoped = [
        proxy
        for proxy in all_proxies
        if proxy.get("environment_name") == environment_name
    ]

    proxies = transform(scoped)
    load_proxies(neo4j_session, proxies, environment_id, update_tag)

    ips = transform_ips(scoped, environment_name)
    load_proxy_ips(neo4j_session, ips, environment_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
    return proxies


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # `proxy_ips` is a nested list consumed by transform_ips; it must not reach the node loader.
    return [
        {key: value for key, value in proxy.items() if key != "proxy_ips"}
        for proxy in raw
    ]


def transform_ips(
    raw: list[dict[str, Any]], environment_name: str
) -> list[dict[str, Any]]:
    ips = []
    for proxy in raw:
        for ip in proxy.get("proxy_ips") or []:
            ips.append(
                {
                    # Modal gives proxy IPs no id of their own.
                    "id": f"{proxy['id']}/{ip['ip_address']}",
                    "ip_address": ip["ip_address"],
                    "status": ip.get("status"),
                    "created_at": ip.get("created_at"),
                    "proxy_id": proxy["id"],
                    "environment_name": environment_name,
                }
            )
    return ips


@timeit
def load_proxies(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalProxySchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def load_proxy_ips(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalProxyIPSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ModalProxyIPSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ModalProxySchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_for_environment(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    environment_id: str,
    update_tag: int,
) -> None:
    """Tear down this resource for one environment, by id. See `environments` for why."""
    cleanup(
        neo4j_session,
        {
            "UPDATE_TAG": update_tag,
            "WORKSPACE_ID": workspace_id,
            "ENVIRONMENT_ID": environment_id,
        },
    )
