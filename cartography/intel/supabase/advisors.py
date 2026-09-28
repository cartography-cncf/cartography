import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import TOLERATED_STATUSES
from cartography.intel.supabase.util import warn_unavailable
from cartography.models.supabase.advisorfinding import (
    SupabaseSecurityAdvisorFindingSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    project_ref = common_job_parameters["PROJECT_REF"]
    advisors = get(api_session, common_job_parameters["BASE_URL"], project_ref)
    if advisors is None:
        warn_unavailable("security advisor findings", project_ref)
        return
    load_findings(
        neo4j_session,
        transform_findings(advisors, project_ref),
        project_ref,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> dict[str, Any]:
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/advisors/security",
        tolerate=TOLERATED_STATUSES,
    )


def transform_findings(
    advisors: dict[str, Any] | None,
    project_ref: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for lint in (advisors or {}).get("lints") or []:
        metadata = lint.get("metadata") or {}
        result.append(
            {
                "id": f"{project_ref}/{lint['cache_key']}",
                "name": lint["name"],
                "title": lint["title"],
                "level": lint.get("level"),
                "facing": lint.get("facing"),
                "categories": lint.get("categories"),
                "description": lint.get("description"),
                "detail": lint.get("detail"),
                "remediation": lint.get("remediation"),
                "entity": metadata.get("entity"),
                "entity_schema": metadata.get("schema"),
                "entity_name": metadata.get("name"),
                "entity_type": metadata.get("type"),
                "database_id": f"{project_ref}/postgres",
            },
        )
    return result


@timeit
def load_findings(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseSecurityAdvisorFindingSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SupabaseSecurityAdvisorFindingSchema(),
        common_job_parameters,
    ).run(neo4j_session)
