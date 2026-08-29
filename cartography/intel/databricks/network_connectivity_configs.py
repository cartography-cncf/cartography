from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks._account_scope import account_scoped_id
from cartography.intel.databricks.util import DatabricksAccountClient
from cartography.models.databricks.network_connectivity_config import (
    DatabricksNetworkConnectivityConfigSchema,
)
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksAccountClient,
    account_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    nccs = get(api_session)
    transformed = transform(nccs, account_id)
    load_network_connectivity_configs(
        neo4j_session, transformed, account_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksAccountClient) -> list[dict[str, Any]]:
    # The NCC listing paginates with a next_page_token and returns items under
    # the ``items`` key, so reuse the Unity Catalog pagination helper.
    return api_session.uc_list(
        api_session.account_uri("/network-connectivity-configs"), "items"
    )


@timeit
def transform(nccs: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for n in nccs:
        ncc_id = n["network_connectivity_config_id"]
        # Flatten the default egress rules' target regions into a single list;
        # the nested rule objects carry no id and are only a coarse egress signal.
        default_rules = (n.get("egress_config") or {}).get("default_rules") or {}
        target_regions: list[str] = []
        for rule in default_rules.values():
            if isinstance(rule, dict):
                regions = rule.get("target_region") or rule.get("target_regions")
                if isinstance(regions, list):
                    target_regions.extend(str(r) for r in regions)
                elif regions:
                    target_regions.append(str(regions))
        result.append(
            {
                "id": account_scoped_id(account_id, ncc_id),
                "network_connectivity_config_id": ncc_id,
                "name": n.get("name"),
                "region": n.get("region"),
                "default_rules_target_regions": target_regions,
            }
        )
    return result


@timeit
def load_network_connectivity_configs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksNetworkConnectivityConfigSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksNetworkConnectivityConfigSchema(), common_job_parameters
    ).run(neo4j_session)
