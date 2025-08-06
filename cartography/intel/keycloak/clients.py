import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.keycloak.util import get_paginated
from cartography.models.keycloak.client import KeycloakClientSchema
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
) -> list[dict]:
    clients = get(
        api_session,
        base_url,
        common_job_parameters["REALM"],
    )
    load_clients(
        neo4j_session,
        clients,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return clients


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    realm: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    url = f"{base_url}/admin/realms/{realm}/clients"
    for client in get_paginated(
        api_session, url, params={"briefRepresentation": False}
    ):
        result.append(client)
        # Get service account user for each client
    # WIP: Get /admin/realms/{realm}/clients/{client-uuid}/service-account-user
    # WIP: Flows override:
    """
      "authenticationFlowBindingOverrides": {
    "browser": "c6b00370-c17d-4ce6-9bd9-385660a60436"
    },
    """

    return result


@timeit
def load_clients(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Keycloak Clients (%s) into Neo4j.", len(data), realm)
    load(
        neo4j_session,
        KeycloakClientSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(KeycloakClientSchema(), common_job_parameters).run(
        neo4j_session
    )
