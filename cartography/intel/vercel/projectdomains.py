import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.vercel.util import paginated_get
from cartography.models.vercel.domain import VercelDomainFromProjectSchema
from cartography.models.vercel.domain import VercelProjectToDomainRel
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    project_id: str,
) -> None:
    project_domains = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["TEAM_ID"],
        project_id,
    )
    load_project_domain_nodes(
        neo4j_session,
        project_domains,
        common_job_parameters["UPDATE_TAG"],
    )
    load_project_domain_rels(
        neo4j_session,
        project_domains,
        project_id,
        common_job_parameters["TEAM_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, project_id, common_job_parameters["UPDATE_TAG"])


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    team_id: str,
    project_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/v9/projects/{project_id}/domains",
        "domains",
        team_id,
    )


@timeit
def load_project_domain_nodes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    # Upsert VercelDomain nodes with minimal fields so any domain attached to
    # a project (including auto-generated *.vercel.app and external domains) is
    # represented. Team-level fields set via VercelDomainSchema are preserved.
    load(
        neo4j_session,
        VercelDomainFromProjectSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def load_project_domain_rels(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    team_id: str,
    update_tag: int,
) -> None:
    rel_data = [
        {
            **d,
            "project_id": project_id,
            "project_domain_id": d.get("id"),
        }
        for d in data
    ]
    load_matchlinks(
        neo4j_session,
        VercelProjectToDomainRel(),
        rel_data,
        lastupdated=update_tag,
        _sub_resource_label="VercelProject",
        _sub_resource_id=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    project_id: str,
    update_tag: int,
) -> None:
    GraphJob.from_matchlink(
        VercelProjectToDomainRel(),
        "VercelProject",
        project_id,
        update_tag,
    ).run(neo4j_session)
