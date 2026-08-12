import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snyk.util import attributes
from cartography.intel.snyk.util import list_jsonapi_resources
from cartography.intel.snyk.util import relationship_id
from cartography.intel.snyk.util import require_id
from cartography.models.snyk.project import SnykProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get(session: requests.Session, base_url: str, org_id: str) -> list[dict[str, Any]]:
    return list_jsonapi_resources(session, f"{base_url}/orgs/{org_id}/projects")


def transform(projects: list[dict[str, Any]], org_id: str) -> list[dict[str, Any]]:
    result = []
    for project in projects:
        attrs = attributes(project)
        result.append(
            {
                "id": require_id(project, "project"),
                "name": attrs.get("name"),
                "type": attrs.get("type"),
                "origin": attrs.get("origin"),
                "target_reference": attrs.get("target_reference")
                or attrs.get("targetReference"),
                "created_at": attrs.get("created_at") or attrs.get("created"),
                "target_id": relationship_id(project, "target"),
                "org_id": org_id,
            }
        )
    return result


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnykProjectSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SnykProjectSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    base_url: str,
    org_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    data = transform(get(session, base_url, org_id), org_id)
    load_projects(neo4j_session, data, org_id, update_tag)
