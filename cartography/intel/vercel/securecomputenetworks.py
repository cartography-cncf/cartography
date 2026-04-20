import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.securecomputenetwork import VercelNetworkToProjectRel
from cartography.models.vercel.securecomputenetwork import (
    VercelSecureComputeNetworkSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    projects: list[dict[str, Any]],
) -> None:
    networks = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
    )
    attachments = transform_network_attachments(projects)
    load_networks(
        neo4j_session,
        networks,
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    load_network_project_rels(
        neo4j_session,
        attachments,
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/v1/connect/networks",
        "networks",
        team_id,
    )


def transform_network_attachments(
    projects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    # The /v1/connect/networks response only exposes a flat list of project
    # IDs. The per-environment scoping and passive/active mode live on the
    # project side, in `connectConfigurations`. We read that here and fold it
    # into one (network, project) attachment per pair, with `environments` and
    # `passive_environments` as aligned lists.
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for project in projects:
        project_id = project.get("id")
        if not project_id:
            continue
        configs = project.get("connectConfigurations") or []
        for config in configs:
            network_id = config.get("connectConfigurationId")
            env_id = config.get("envId")
            if not network_id or not env_id:
                continue
            key = (network_id, project_id)
            entry = grouped.setdefault(
                key,
                {
                    "networkId": network_id,
                    "projectId": project_id,
                    "environments": [],
                    "passive_environments": [],
                },
            )
            entry["environments"].append(env_id)
            if config.get("passive"):
                entry["passive_environments"].append(env_id)
    return list(grouped.values())


@timeit
def load_networks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        VercelSecureComputeNetworkSchema(),
        data,
        lastupdated=update_tag,
        TEAM_ID=team_id,
    )


@timeit
def load_network_project_rels(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    team_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        VercelNetworkToProjectRel(),
        data,
        lastupdated=update_tag,
        _sub_resource_label="VercelTeam",
        _sub_resource_id=team_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        VercelSecureComputeNetworkSchema(), common_job_parameters
    ).run(
        neo4j_session,
    )
    GraphJob.from_matchlink(
        VercelNetworkToProjectRel(),
        "VercelTeam",
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
