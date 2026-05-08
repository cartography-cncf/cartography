import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sentinelone.api import build_scope_params
from cartography.intel.sentinelone.api import get_paginated_results
from cartography.models.sentinelone.agent import S1AgentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_agents(
    api_url: str,
    api_token: str,
    account_id: str | None = None,
    site_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Get agent data from SentinelOne API
    :param api_url: The SentinelOne API URL
    :param api_token: The SentinelOne API token
    :param account_id: The SentinelOne account ID
    :param site_id: Optional SentinelOne site ID for site-scoped syncs
    :return: Raw agent data from API
    """
    logger.info(f"Retrieving SentinelOne agent data for account {account_id}")

    params = build_scope_params(account_id=account_id, site_id=site_id)
    params["limit"] = 1000
    agents = get_paginated_results(
        api_url=api_url,
        endpoint="web/api/v2.1/agents",
        api_token=api_token,
        params=params,
    )

    logger.debug(
        "Retrieved %s agents from SentinelOne account %s", len(agents), account_id
    )
    return agents


@timeit
def transform_agents(agent_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform SentinelOne agent data for loading into Neo4j
    :param agent_list: Raw agent data from the API
    :return: Transformed agent data
    """
    result: list[dict[str, Any]] = []

    for agent in agent_list:
        transformed_agent = {
            # Required fields - use direct access (will raise KeyError if missing)
            "id": agent["id"],
            # Optional fields - use .get() with None default
            "uuid": agent.get("uuid"),
            "computer_name": agent.get("computerName"),
            "firewall_enabled": agent.get("firewallEnabled"),
            "os_name": agent.get("osName"),
            "os_revision": agent.get("osRevision"),
            "domain": agent.get("domain"),
            "last_active": agent.get("lastActiveDate"),
            "last_successful_scan": agent.get("lastSuccessfulScanDate"),
            "scan_status": agent.get("scanStatus"),
            "serial_number": agent.get("serialNumber"),
        }
        result.append(transformed_agent)

    return result


@timeit
def load_agents(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    """
    Load SentinelOne agent data into Neo4j
    :param neo4j_session: Neo4j session
    :param data: The transformed agent data
    :param account_id: The SentinelOne account ID
    :param update_tag: Update tag for tracking data freshness
    :return: None
    """
    load(
        neo4j_session,
        S1AgentSchema(),
        data,
        lastupdated=update_tag,
        S1_ACCOUNT_ID=account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Remove stale SentinelOne agent data from Neo4j
    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters for cleanup
    :return: None
    """
    logger.debug("Running S1Agent cleanup job")
    GraphJob.from_node_schema(S1AgentSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    *,
    do_cleanup: bool = True,
) -> None:
    """
    Sync SentinelOne agents using the standard sync pattern
    :param neo4j_session: Neo4j session
    :param common_job_parameters: Common job parameters containing API_URL, API_TOKEN, S1_ACCOUNT_ID, UPDATE_TAG
    :return: None
    """
    api_url = common_job_parameters["API_URL"]
    api_token = common_job_parameters["API_TOKEN"]
    account_id = common_job_parameters["S1_ACCOUNT_ID"]
    site_id = common_job_parameters.get("S1_SITE_ID")
    update_tag = common_job_parameters["UPDATE_TAG"]

    logger.info(f"Syncing SentinelOne agent data for account {account_id}")

    # 1. GET - Fetch data from API
    agents_raw_data = get_agents(api_url, api_token, account_id, site_id)

    # 2. TRANSFORM - Shape data for ingestion
    transformed_data = transform_agents(agents_raw_data)

    # 3. LOAD - Ingest to Neo4j using data model
    load_agents(neo4j_session, transformed_data, account_id, update_tag)

    # 4. CLEANUP - Remove stale data
    if do_cleanup:
        cleanup(neo4j_session, common_job_parameters)
