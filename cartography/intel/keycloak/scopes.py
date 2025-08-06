import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.keycloak.util import get_paginated
from cartography.models.keycloak.scope import KeycloakScopeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    scopes = get(
        api_session,
        base_url,
        common_job_parameters["REALM"],
    )
    load_scopes(
        neo4j_session,
        scopes,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return scopes


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    realm: str,
) -> list[dict[str, Any]]:
    url = f"{base_url}/admin/realms/{realm}/client-scopes"
    return list(get_paginated(api_session, url, params={"briefRepresentation": False}))


@timeit
def load_scopes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Keycloak Scopes (%s) into Neo4j.", len(data), realm)
    load(
        neo4j_session,
        KeycloakScopeSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(KeycloakScopeSchema(), common_job_parameters).run(
        neo4j_session
    )
