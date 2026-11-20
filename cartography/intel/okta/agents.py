from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from datetime import timezone
from typing import Any

import neo4j
from okta.client import Client as OktaClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.okta.common import collect_raw_paginated
from cartography.intel.okta.common import is_missing_scope_error
from cartography.intel.okta.common import OKTA_MISSING_SCOPE_WARNING
from cartography.intel.okta.common import OktaApiError
from cartography.models.okta.agent import OktaAgentSchema
from cartography.models.okta.agent_pool import OktaAgentPoolSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def _get_okta_agent_pools(okta_client: OktaClient) -> list[dict[str, Any]]:
    return await collect_raw_paginated(okta_client, "/api/v1/agentPools")


def _epoch_millis_to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)


def _transform_okta_agent_pools(
    agent_pools: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pools: list[dict[str, Any]] = []
    agents: list[dict[str, Any]] = []
    for pool in agent_pools:
        pools.append(
            {
                "id": pool["id"],
                "name": pool.get("name"),
                "type": pool.get("type"),
                "operational_status": pool.get("operationalStatus"),
                "disrupted_agents": pool.get("disruptedAgents"),
                "inactive_agents": pool.get("inactiveAgents"),
            },
        )
        for agent in pool.get("agents") or []:
            agents.append(
                {
                    "id": agent["id"],
                    "name": agent.get("name"),
                    "type": agent.get("type") or pool.get("type"),
                    "version": agent.get("version"),
                    "is_latest_ga_version": agent.get("isLatestGAedVersion"),
                    "is_hidden": agent.get("isHidden"),
                    "operational_status": agent.get("operationalStatus"),
                    "last_connection": _epoch_millis_to_datetime(
                        agent.get("lastConnection"),
                    ),
                    "update_status": agent.get("updateStatus"),
                    "update_message": agent.get("updateMessage"),
                    "pool_id": agent.get("poolId") or pool["id"],
                },
            )
    return pools, agents


def _load_okta_agent_pools(
    neo4j_session: neo4j.Session,
    pools: list[dict[str, Any]],
    agents: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        OktaAgentPoolSchema(),
        pools,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
    )
    load(
        neo4j_session,
        OktaAgentSchema(),
        agents,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
    )


def _cleanup_okta_agent_pools(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(OktaAgentSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(OktaAgentPoolSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_okta_agent_pools(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> bool:
    """Sync Okta agent pools and their agents, and return whether the credential could read them."""
    logger.info("Syncing Okta agent pools")
    try:
        raw_agent_pools = asyncio.run(_get_okta_agent_pools(okta_client))
    except OktaApiError as exc:
        if is_missing_scope_error(exc):
            logger.warning(
                OKTA_MISSING_SCOPE_WARNING,
                "Okta agent pools",
                "okta.agentPools.read",
            )
            return False
        raise
    pools, agents = _transform_okta_agent_pools(raw_agent_pools)
    _load_okta_agent_pools(neo4j_session, pools, agents, common_job_parameters)
    _cleanup_okta_agent_pools(neo4j_session, common_job_parameters)
    logger.info("Loaded %s Okta agent pools and %s agents", len(pools), len(agents))
    return True
