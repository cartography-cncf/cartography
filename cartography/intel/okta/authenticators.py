# Okta intel module - Authenticators
import asyncio
import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from okta.client import Client as OktaClient
from okta.models.authenticator import Authenticator as OktaAuthenticator

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.okta.authenticator import OktaAuthenticatorSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_okta_authenticators(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
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
async def _get_okta_authenticators(okta_client: OktaClient) -> List[OktaAuthenticator]:
    """
    Get Okta authenticators list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta authenticators
    """

    authenticators, _, _ = await okta_client.list_authenticators()
    return authenticators


@timeit
def _transform_okta_authenticators(
    okta_authenticators: List[OktaAuthenticator],
) -> List[Dict[str, Any]]:
    """
    Convert a list of Okta authenticators into a format for Neo4j
    :param okta_authenticators: List of Okta authenticators
    :return: List of authenticators dicts
    """
    transformed_authenticators: List[Dict] = []
    logger.info(f"Transforming {len(okta_authenticators)} Okta Authenticators")
    for okta_authenticator in okta_authenticators:
        authenticator_props = {}
        authenticator_props["id"] = okta_authenticator.id
        authenticator_props["created"] = okta_authenticator.created
        authenticator_props["key"] = okta_authenticator.key
        authenticator_props["last_updated"] = okta_authenticator.last_updated
        authenticator_props["name"] = okta_authenticator.name
        # Not all authenticators have providers or settings configured
        # TODO: Parsing out these parameters would provide greater flexibility
        # For now we just dump these to dicts and provide as JSON strings
        if okta_authenticator.provider:
            authenticator_props["provider_type"] = okta_authenticator.provider.type
            authenticator_props["provider_configuration"] = json.dumps(
                okta_authenticator.provider.configuration.as_dict()
            )
        if okta_authenticator.settings:
            authenticator_props["settings"] = json.dumps(
                okta_authenticator.settings.as_dict()
            )
        authenticator_props["status"] = okta_authenticator.status
        authenticator_props["authenticator_type"] = okta_authenticator.type
        transformed_authenticators.append(authenticator_props)
    return transformed_authenticators


@timeit
def _load_okta_authenticators(
    neo4j_session: neo4j.Session,
    authenticator_list: List[Dict],
    common_job_parameters: Dict[str, Any],
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
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
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
