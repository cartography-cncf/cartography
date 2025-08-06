import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.keycloak.util import get_paginated
from cartography.models.keycloak.role import KeycloakRoleSchema
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
    client_ids: list[str],
) -> None:
    roles = get(api_session, base_url, common_job_parameters["REALM"], client_ids)
    load_roles(
        neo4j_session,
        roles,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session, base_url: str, realm: str, client_ids: list[str]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    # Get roles at the REALM level
    url = f"{base_url}/admin/realms/{realm}/roles"
    for role in get_paginated(api_session, url, params={"briefRepresentation": False}):
        result.append(role)
        # WIP: Get composite roles
    # Get roles for each client
    for client_id in client_ids:
        url = f"{base_url}/admin/realms/{realm}/clients/{client_id}/roles"
        for role in get_paginated(
            api_session, url, params={"briefRepresentation": False}
        ):
            result.append(role)
            # WIP: Get composite roles
    return result


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Keycloak Roles (%s) into Neo4j.", len(data), realm)
    load(
        neo4j_session,
        KeycloakRoleSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(KeycloakRoleSchema(), common_job_parameters).run(
        neo4j_session
    )
