import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.intel.snyk.util import attributes
from cartography.intel.snyk.util import get_jsonapi_resource
from cartography.intel.snyk.util import require_id
from cartography.models.snyk.org import SnykOrgSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get(session: requests.Session, base_url: str, org_id: str) -> dict[str, Any]:
    return get_jsonapi_resource(session, f"{base_url}/orgs/{org_id}")


def transform(org: dict[str, Any]) -> dict[str, Any]:
    attrs = attributes(org)
    return {
        "id": require_id(org, "org"),
        "name": attrs.get("name"),
        "slug": attrs.get("slug"),
        "group_id": attrs.get("group_id"),
    }


@timeit
def load_org(
    neo4j_session: neo4j.Session,
    org: dict[str, Any],
    update_tag: int,
) -> None:
    load(neo4j_session, SnykOrgSchema(), [org], lastupdated=update_tag)


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    run_write_query(
        neo4j_session,
        """
        MATCH (org:SnykOrg)
        WHERE org.id = $ORG_ID AND org.lastupdated <> $UPDATE_TAG
        OPTIONAL MATCH (org)-[:RESOURCE]->(resource)
        WHERE resource:SnykTarget OR resource:SnykProject OR resource:SnykIssue
        DETACH DELETE org, resource
        """,
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
        ORG_ID=common_job_parameters["ORG_ID"],
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
    org = transform(get(session, base_url, org_id))
    load_org(neo4j_session, org, update_tag)
    common_job_parameters["ORG_ID"] = org["id"]
