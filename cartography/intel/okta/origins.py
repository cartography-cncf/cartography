# Okta intel module - Origins
import asyncio
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from okta.client import Client as OktaClient
from okta.models.trusted_origin import TrustedOrigin as OktaTrustedOrigin

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.okta.origin import OktaTrustedOriginSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_okta_origins(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync Okta origins
    :param okta_client: An Okta client object
    :param neo4j_session: Session with Neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    logger.info("Syncing Okta origins")
    origins = asyncio.run(_get_okta_origins(okta_client))
    transformed_origins = _transform_okta_origins(origins)
    _load_okta_origins(neo4j_session, transformed_origins, common_job_parameters)
    _cleanup_okta_origins(neo4j_session, common_job_parameters)


@timeit
async def _get_okta_origins(okta_client: OktaClient) -> List[OktaTrustedOrigin]:
    """
    Get Okta origins list from Okta
    :param okta_client: An Okta client object
    :return: List of Okta origins
    """
    output_origins = []
    query_parameters = {"limit": 200}
    origins, resp, err = await okta_client.list_origins(query_parameters)
    if err:
        raise err

    output_origins += origins
    while resp.has_next():
        origins, err = await resp.next()
        if err:
            raise err
        output_origins += origins
        logger.debug("Fetched %s origins", len(origins))
    return output_origins


@timeit
def _transform_okta_origins(
    okta_origins: List[OktaTrustedOrigin],
) -> List[Dict[str, Any]]:
    """
    Convert a list of Okta origins into a format for Neo4j
    :param okta_origins: List of Okta origins
    :return: List of origin dicts
    """
    transformed_origins: List[Dict] = []
    logger.info("Transforming %s Okta origins", len(okta_origins))
    for okta_origin in okta_origins:
        origin_props: Dict[str, Any] = {}
        origin_props["id"] = okta_origin.id
        origin_props["created"] = okta_origin.created
        origin_props["created_by"] = okta_origin.created_by
        origin_props["last_updated"] = okta_origin.last_updated
        origin_props["last_updated_by"] = okta_origin.last_updated_by
        origin_props["name"] = okta_origin.name
        origin_props["origin"] = okta_origin.origin
        # Scopes have a specific type
        # currently supported are CORS, Redirect, and IFrame
        for scope in okta_origin.scopes:
            apps = []
            for app in scope.allowed_okta_apps:
                apps.append(app.value)
            if scope.type.value == "CORS":
                origin_props["cors_allowed_okta_apps"] = apps
                origin_props["cors_allowed"] = True
            elif scope.type.value == "REDIRECT":
                origin_props["redirect_allowed_okta_apps"] = apps
                origin_props["redirect_allowed"] = True
            elif scope.type.value == "IFRAME_EMBED":
                origin_props["iframe_allowed_okta_apps"] = apps
                origin_props["iframe_allowed"] = True
        origin_props["status"] = okta_origin.status
        transformed_origins.append(origin_props)
    return transformed_origins


@timeit
def _load_okta_origins(
    neo4j_session: neo4j.Session,
    origin_list: List[Dict],
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Load Okta origins information into the graph
    :param neo4j_session: session with neo4j server
    :param origin_list: list of origins
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """

    logger.info("Loading %s Okta origins", len(origin_list))

    load(
        neo4j_session,
        OktaTrustedOriginSchema(),
        origin_list,
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
        lastupdated=common_job_parameters["UPDATE_TAG"],
    )


@timeit
def _cleanup_okta_origins(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Cleanup origin nodes and relationships
    :param neo4j_session: session with neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    GraphJob.from_node_schema(OktaTrustedOriginSchema(), common_job_parameters).run(
        neo4j_session,
    )
