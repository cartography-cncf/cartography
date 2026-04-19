import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.models.socketdev.organization import SocketDevOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)
_BASE_URL = "https://api.socket.dev/v0"


@timeit
def get(api_token: str) -> dict[str, Any]:
    """
    Fetch all organizations from the Socket.dev API.
    Returns the raw API response dict.
    """
    response = requests.get(
        f"{_BASE_URL}/organizations",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/json",
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def transform(raw_response: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Transform the organizations response into a flat list of dicts.
    The API returns { organizations: { org_id: { id, name, slug, plan, ... } } }.
    The dict key is the org ID, not the slug.
    """
    orgs = []
    organizations = raw_response.get("organizations", {})
    for _org_key, org_data in organizations.items():
        orgs.append(
            {
                "id": org_data["id"],
                "name": org_data.get("name"),
                "slug": org_data["slug"],
                "plan": org_data.get("plan"),
                "image": org_data.get("image"),
            },
        )
    return orgs


@timeit
def load_organizations(
    neo4j_session: neo4j.Session,
    organizations: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SocketDevOrganizationSchema(),
        organizations,
        lastupdated=update_tag,
    )


@timeit
def sync_organizations(
    neo4j_session: neo4j.Session,
    api_token: str,
    update_tag: int,
) -> list[dict[str, Any]]:
    """
    Sync Socket.dev organizations.
    Returns the list of transformed organizations for the caller to iterate over.
    """
    logger.info("Starting Socket.dev organizations sync")
    raw_response = get(api_token)
    organizations = transform(raw_response)

    if not organizations:
        logger.warning("No Socket.dev organizations found.")
        return []

    load_organizations(neo4j_session, organizations, update_tag)
    logger.info(
        "Completed Socket.dev organizations sync (%d orgs)",
        len(organizations),
    )
    return organizations
