from __future__ import annotations

# Okta intel module - Authenticators
import asyncio
import json
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient
from okta.models.authenticator_base import AuthenticatorBase as OktaAuthenticator

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.okta.authenticator import OktaAuthenticatorSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_okta_authenticators(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Okta authenticators
    :param okta_client: An Okta client object
    :param neo4j_session: Session with Neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Syncing Okta authenticators")
    authenticators = asyncio.run(_get_okta_authenticators(okta_client))
    transformed_authenticators = _transform_okta_authenticators(authenticators)
    _load_okta_authenticators(
        neo4j_session, transformed_authenticators, common_job_parameters
    )
    _cleanup_okta_authenticators(neo4j_session, common_job_parameters)


@timeit
async def _get_okta_authenticators(okta_client: OktaClient) -> list[OktaAuthenticator]:
    """
    Get Okta authenticators list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta authenticators
    """

    authenticators, _, _ = await okta_client.list_authenticators()
    return authenticators


@timeit
def _transform_okta_authenticators(
    okta_authenticators: list[OktaAuthenticator],
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta authenticators into a format for Neo4j
    :param okta_authenticators: List of Okta authenticators
    :return: List of authenticators dicts
    """
    transformed_authenticators: list[dict] = []
    logger.info(f"Transforming {len(okta_authenticators)} Okta Authenticators")
    for okta_authenticator in okta_authenticators:
        authenticator_props = {}
        authenticator_props["id"] = okta_authenticator.id
        authenticator_props["created"] = okta_authenticator.created
        authenticator_props["key"] = okta_authenticator.key
        authenticator_props["last_updated"] = okta_authenticator.last_updated
        authenticator_props["name"] = okta_authenticator.name
        # Parse provider configuration into separate properties
        if okta_authenticator.provider:
            authenticator_props["provider_type"] = okta_authenticator.provider.type
            provider_config = okta_authenticator.provider.configuration
            if provider_config:
                config_dict = provider_config.as_dict()
                # Common provider configuration fields
                authenticator_props["provider_auth_port"] = config_dict.get("authPort")
                authenticator_props["provider_host_name"] = config_dict.get("hostName")
                authenticator_props["provider_instance_id"] = config_dict.get(
                    "instanceId"
                )
                authenticator_props["provider_integration_key"] = config_dict.get(
                    "integrationKey"
                )
                authenticator_props["provider_secret_key"] = config_dict.get(
                    "secretKey"
                )
                authenticator_props["provider_shared_secret"] = config_dict.get(
                    "sharedSecret"
                )
                authenticator_props["provider_user_name_template"] = config_dict.get(
                    "userNameTemplate", {}
                ).get("template")
                # Keep full configuration as JSON for any additional fields
                authenticator_props["provider_configuration"] = json.dumps(config_dict)
        # Parse settings into separate properties
        if okta_authenticator.settings:
            settings_dict = okta_authenticator.settings.as_dict()
            # Common settings fields
            authenticator_props["settings_allowed_for"] = settings_dict.get(
                "allowedFor"
            )
            authenticator_props["settings_token_lifetime_minutes"] = settings_dict.get(
                "tokenLifetimeInMinutes"
            )
            authenticator_props["settings_compliance"] = settings_dict.get("compliance")
            authenticator_props["settings_channel_binding"] = settings_dict.get(
                "channelBinding", {}
            ).get("style")
            authenticator_props["settings_user_verification"] = settings_dict.get(
                "userVerification"
            )
            authenticator_props["settings_app_instance_id"] = settings_dict.get(
                "appInstanceId"
            )
            # Keep full settings as JSON for any additional fields
            authenticator_props["settings"] = json.dumps(settings_dict)
        authenticator_props["status"] = okta_authenticator.status
        authenticator_props["authenticator_type"] = okta_authenticator.type
        transformed_authenticators.append(authenticator_props)
    return transformed_authenticators


@timeit
def _load_okta_authenticators(
    neo4j_session: neo4j.Session,
    authenticator_list: list[dict],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load Okta authenticator information into the graph
    :param neo4j_session: session with neo4j server
    :param authenticator_list: list of authenticators
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info(f"Loading {len(authenticator_list)} Okta Authenticators")

    load(
        neo4j_session,
        OktaAuthenticatorSchema(),
        authenticator_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_authenticators(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Cleanup authenticator nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaAuthenticatorSchema(), common_job_parameters).run(
        neo4j_session
    )
