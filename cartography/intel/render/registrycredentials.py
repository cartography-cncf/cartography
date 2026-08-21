import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_plain_array
from cartography.intel.render.util import require_non_empty
from cartography.models.render.registrycredential import RenderRegistryCredentialSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    # Single unpaginated GET - see list_plain_array()'s docstring for why this bare-
    # array endpoint has no documented way to fetch a second page. This endpoint
    # documents `limit` with a default of 20 and a max of 100; passing the documented
    # max explicitly avoids truncating a workspace with more than 20 credentials on
    # the default page size. A workspace with more than 100 credentials still raises
    # rather than silently truncating - see list_plain_array()'s `limit` docs.
    return list_plain_array(
        session,
        f"{BASE_URL}/registrycredentials",
        params={"ownerId": [owner_id]},
        limit=100,
    )


def transform(
    registry_credentials: list[dict[str, Any]], owner_id: str
) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(credential.get("id"), "registry credential id"),
            "name": credential.get("name"),
            "ownerId": owner_id,
            "username": credential.get("username"),
            "registry": credential.get("registry"),
            "updatedAt": credential.get("updatedAt"),
        }
        for credential in registry_credentials
    ]


@timeit
def load_registry_credentials(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderRegistryCredentialSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        RenderRegistryCredentialSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    registry_credentials = get(session, owner_id)
    transformed = transform(registry_credentials, owner_id)
    load_registry_credentials(neo4j_session, transformed, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
