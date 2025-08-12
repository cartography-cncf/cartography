import logging

import neo4j
import requests

import cartography.intel.keycloak.authenticationexecutions
import cartography.intel.keycloak.authenticationflows
import cartography.intel.keycloak.clients
import cartography.intel.keycloak.groups
import cartography.intel.keycloak.identityproviders
import cartography.intel.keycloak.organizations
import cartography.intel.keycloak.realms
import cartography.intel.keycloak.roles
import cartography.intel.keycloak.scopes
import cartography.intel.keycloak.users
from cartography.config import Config
from cartography.util import timeit

logger = logging.getLogger(__name__)
_TIMEOUT = (60, 60)


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
    with requests.session() as api_session:
        payload = {
            "grant_type": "client_credentials",
            "client_id": config.keycloak_client_id,
            "client_secret": config.keycloak_client_secret,
        }
        req = api_session.post(
            f"{config.keycloak_url}/realms/{config.keycloak_realm}/protocol/openid-connect/token",
            data=payload,
            timeout=_TIMEOUT,
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
                "REALM_ID": realm["id"],
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
            scopes = cartography.intel.keycloak.scopes.sync(
                neo4j_session,
                api_session,
                config.keycloak_url,
                realm_scopped_job_parameters,
            )
            scope_ids = [s["id"] for s in scopes]
            flows = cartography.intel.keycloak.authenticationflows.sync(
                neo4j_session,
                api_session,
                config.keycloak_url,
                realm_scopped_job_parameters,
            )
            flow_aliases_to_id = {f["alias"]: f["id"] for f in flows}
            cartography.intel.keycloak.authenticationexecutions.sync(
                neo4j_session,
                api_session,
                config.keycloak_url,
                realm_scopped_job_parameters,
                list(flow_aliases_to_id.keys()),
            )
            realm_default_flows = {
                "browser": flow_aliases_to_id.get(realm.get("browserFlow")),
                "registration": flow_aliases_to_id.get(realm.get("registrationFlow")),
                "direct_grant": flow_aliases_to_id.get(realm.get("directGrantFlow")),
                "reset_credentials": flow_aliases_to_id.get(
                    realm.get("resetCredentialsFlow")
                ),
                "client_authentication": flow_aliases_to_id.get(
                    realm.get("clientAuthenticationFlow")
                ),
                "docker_authentication": flow_aliases_to_id.get(
                    realm.get("dockerAuthenticationFlow")
                ),
                "first_broker_login": flow_aliases_to_id.get(
                    realm.get("firstBrokerLoginFlow")
                ),
            }

            clients = cartography.intel.keycloak.clients.sync(
                neo4j_session,
                api_session,
                config.keycloak_url,
                realm_scopped_job_parameters,
                realm_default_flows,
            )
            client_ids = [c["id"] for c in clients]
            cartography.intel.keycloak.roles.sync(
                neo4j_session,
                api_session,
                config.keycloak_url,
                realm_scopped_job_parameters,
                client_ids,
                scope_ids,
            )
            cartography.intel.keycloak.groups.sync(
                neo4j_session,
                api_session,
                config.keycloak_url,
                realm_scopped_job_parameters,
            )

            # Organizations if they are enabled
            if realm.get("organizationsEnabled", False):
                cartography.intel.keycloak.organizations.sync(
                    neo4j_session,
                    api_session,
                    config.keycloak_url,
                    realm_scopped_job_parameters,
                )
