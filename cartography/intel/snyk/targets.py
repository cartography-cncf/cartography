import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snyk.util import attributes
from cartography.intel.snyk.util import list_jsonapi_resources
from cartography.intel.snyk.util import require_id
from cartography.models.snyk.target import SnykTargetSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get(session: requests.Session, base_url: str, org_id: str) -> list[dict[str, Any]]:
    return list_jsonapi_resources(session, f"{base_url}/orgs/{org_id}/targets")


def transform(targets: list[dict[str, Any]], org_id: str) -> list[dict[str, Any]]:
    result = []
    for target in targets:
        attrs = attributes(target)
        result.append(
            {
                "id": require_id(target, "target"),
                "display_name": attrs.get("display_name") or attrs.get("displayName"),
                "url": attrs.get("url") or attrs.get("remote_url"),
                "origin": attrs.get("origin"),
                "org_id": org_id,
            }
        )
    return result


@timeit
def load_targets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnykTargetSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SnykTargetSchema(), common_job_parameters).run(
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
    load_targets(neo4j_session, data, org_id, update_tag)
