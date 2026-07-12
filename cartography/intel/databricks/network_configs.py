from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.network_config import DatabricksNetworkConfigSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    networks = get(api_session)
    transformed = transform(networks, account_id)
    load_network_configs(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    return api_session.get(api_session.account_uri("/networks")) or []


@timeit
def transform(networks: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for n in networks:
        network_id = n["network_id"]
        # vpc_status is reported nested under error_messages/vpc_status depending
        # on the workspace state; the top-level field is the stable signal.
        result.append(
            {
                "id": account_scoped_id(account_id, network_id),
                "network_id": network_id,
                "network_name": n.get("network_name"),
                "vpc_id": n.get("vpc_id"),
                "subnet_ids": n.get("subnet_ids") or [],
                "security_group_ids": n.get("security_group_ids") or [],
                "vpc_status": n.get("vpc_status"),
            }
        )
    return result


@timeit
def load_network_configs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksNetworkConfigSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksNetworkConfigSchema(), common_job_parameters
    ).run(neo4j_session)
