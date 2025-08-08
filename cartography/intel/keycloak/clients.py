import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.keycloak.util import get_paginated
from cartography.models.keycloak.client import KeycloakClientSchema
from cartography.models.keycloak.user import KeycloakUserSchema
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
    transformed_clients, service_accounts = transform(clients)

    # WIP: Flows override:
    """
      "authenticationFlowBindingOverrides": {
    "browser": "c6b00370-c17d-4ce6-9bd9-385660a60436"
    },
    """
    load_service_accounts(
        neo4j_session,
        service_accounts,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
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
        # Check if the client has a service account user
        if "service_account" in client.get("defaultClientScopes", []):
            # Get service account user for each client
            service_account_url = f"{base_url}/admin/realms/{realm}/clients/{client['id']}/service-account-user"
            sa_req = api_session.get(
                service_account_url,
                timeout=_TIMEOUT,
                params={"briefRepresentation": False},
            )
            sa_req.raise_for_status()
            client["service_account_user"] = sa_req.json()
        result.append(client)
    return result


def transform(
    clients: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    transformed_clients = []
    service_accounts = []
    for client in clients:
        sa = client.get("service_account_user")
        if sa:
            service_accounts.append(sa)
            client.pop("service_account_user", None)
            client["_service_account_user_id"] = sa["id"]
        transformed_clients.append(client)
    return transformed_clients, service_accounts


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
def load_service_accounts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d Keycloak Service Accounts (%s) into Neo4j.", len(data), realm
    )
    load(
        neo4j_session,
        KeycloakUserSchema(),
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
    # It's OK to cleanup users here as it will not clean the regular users (which have the same UPDATE_TAG)
    GraphJob.from_node_schema(KeycloakUserSchema(), common_job_parameters).run(
        neo4j_session
    )
