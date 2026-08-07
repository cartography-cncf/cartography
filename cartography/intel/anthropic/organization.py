from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.models.anthropic.organization import AnthropicOrganizationSchema
from cartography.util import timeit

# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> str:
    """Load the organization node and return its id, which scopes every other sync."""
    organization = get(api_session, common_job_parameters["BASE_URL"])
    common_job_parameters["ORG_ID"] = organization["id"]
    load_organization(neo4j_session, organization, common_job_parameters["UPDATE_TAG"])
    # No cleanup: the organization is the sub-resource every other node hangs off, so
    # it has no parent to scope a cleanup job to.
    return organization["id"]


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> dict[str, Any]:
    req = api_session.get(f"{base_url}/organizations/me", timeout=_TIMEOUT)
    req.raise_for_status()
    result: dict[str, Any] = req.json()
    return result


@timeit
def load_organization(
    neo4j_session: neo4j.Session,
    data: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AnthropicOrganizationSchema(),
        [data],
        lastupdated=update_tag,
    )
