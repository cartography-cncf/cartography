import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.intel.pylon.util import get_object
from cartography.models.pylon.organization import PylonOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> str:
    me = get(api_session, base_url)
    organization = transform(me, base_url)
    load_organization(
        neo4j_session,
        organization,
        common_job_parameters["UPDATE_TAG"],
    )
    return organization["id"]


@timeit
def get(api_session: requests.Session, base_url: str) -> dict[str, Any]:
    return get_object(api_session, f"{base_url}/me")


def transform(me: dict[str, Any], base_url: str) -> dict[str, Any]:
    return {
        "id": me["id"],
        "name": me.get("name"),
        "base_url": base_url,
    }


@timeit
def load_organization(
    neo4j_session: neo4j.Session,
    organization: dict[str, Any],
    update_tag: int,
) -> None:
    logger.info("Loading Pylon organization %s", organization["id"])
    load(
        neo4j_session,
        PylonOrganizationSchema(),
        [organization],
        lastupdated=update_tag,
    )
