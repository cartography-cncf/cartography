import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import _TIMEOUT
from cartography.models.vercel.firewallconfig import VercelFirewallConfigSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    project_id: str,
) -> None:
    configs = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
        project_id,
    )
    load_firewall_configs(
        neo4j_session,
        configs,
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
    project_id: str,
) -> list[dict[str, Any]]:
    resp = api_session.get(
        f"{base_url}/v1/security/firewall/config",
        params={"projectId": project_id, "teamId": team_id},
        timeout=_TIMEOUT,
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    config = resp.json()
    config["id"] = f"{project_id}_firewall"
    return [config]


@timeit
def load_firewall_configs(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelFirewallConfigSchema(),
        data,
        lastupdated=update_tag,
        project_id=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(VercelFirewallConfigSchema(), common_job_parameters).run(
        neo4j_session,
    )
