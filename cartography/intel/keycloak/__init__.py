import logging

import neo4j
import requests

import cartography.intel.keycloak.clients
import cartography.intel.keycloak.groups
import cartography.intel.keycloak.identityproviders
import cartography.intel.keycloak.realms
import cartography.intel.keycloak.roles
import cartography.intel.keycloak.scopes
import cartography.intel.keycloak.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_keycloak_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Keycloak data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if (
        not config.keycloak_client_id
        or not config.keycloak_client_secret
        or not config.keycloak_url
        or not config.keycloak_realm
    ):
        logger.info(
            "Keycloak import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    # Create requests sessions
    api_session = requests.session()
    payload = {
        "grant_type": "client_credentials",
        "client_id": config.keycloak_client_id,
        "client_secret": config.keycloak_client_secret,
    }
    req = api_session.post(
        f"{config.keycloak_url}/realms/master/protocol/openid-connect/token",
        data=payload,
    )
    req.raise_for_status()
    api_session.headers.update(
        {"Authorization": f'Bearer {req.json()["access_token"]}'}
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    for realm in cartography.intel.keycloak.realms.sync(
        neo4j_session, api_session, config.keycloak_url, common_job_parameters
    ):
        realm_scopped_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "REALM": realm["realm"],
        }
        cartography.intel.keycloak.users.sync(
            neo4j_session,
            api_session,
            config.keycloak_url,
            realm_scopped_job_parameters,
        )
        cartography.intel.keycloak.identityproviders.sync(
            neo4j_session,
            api_session,
            config.keycloak_url,
            realm_scopped_job_parameters,
        )
        # WIP: Do protocol mappers before scopes
        # WIP: Authentication Flows
        # WIP: Authentication Executions

        scopes = cartography.intel.keycloak.scopes.sync(
            neo4j_session,
            api_session,
            config.keycloak_url,
            realm_scopped_job_parameters,
        )
        scope_ids = [s["id"] for s in scopes]
        clients = cartography.intel.keycloak.clients.sync(
            neo4j_session,
            api_session,
            config.keycloak_url,
            realm_scopped_job_parameters,
        )
        client_ids = [c["id"] for c in clients]
        cartography.intel.keycloak.roles.sync(
            neo4j_session,
            api_session,
            config.keycloak_url,
            realm_scopped_job_parameters,
            client_ids,
        )
        # WIP: Scope Mappings

        cartography.intel.keycloak.groups.sync(
            neo4j_session,
            api_session,
            config.keycloak_url,
            realm_scopped_job_parameters,
        )
