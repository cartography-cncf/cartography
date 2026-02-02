from __future__ import annotations

# Okta intel module - User Factors
import asyncio
import logging
from typing import Any

import neo4j
from okta.client import Client as OktaClient
from okta.models.user_factor import UserFactor

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.okta.factor import OktaUserFactorSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync_okta_user_factors(
    okta_client: OktaClient,
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    user_ids: list[str],
) -> None:
    """
    Sync Okta user factors (MFA methods)
    :param okta_client: An Okta client object
    :param neo4j_session: Session with Neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :param user_ids: List of user IDs to fetch factors for
    :return: Nothing
    """
    logger.info("Syncing Okta user factors")

    all_factors: list[dict[str, Any]] = []
    for user_id in user_ids:
        user_factors = asyncio.run(_get_okta_user_factors(okta_client, user_id))
        transformed = _transform_okta_user_factors(user_factors, user_id)
        all_factors.extend(transformed)

    logger.info("Total factors to load: %s", len(all_factors))
    _load_okta_user_factors(neo4j_session, all_factors, common_job_parameters)
    _cleanup_okta_user_factors(neo4j_session, common_job_parameters)


@timeit
async def _get_okta_user_factors(
    okta_client: OktaClient,
    user_id: str,
) -> list[UserFactor]:
    """
    Get Okta factors for a specific user
    :param okta_client: An Okta client object
    :param user_id: The user ID to fetch factors for
    :return: List of Okta user factors
    """
    factors, _, err = await okta_client.list_factors(user_id)
    if err:
        raise err
    return factors or []


@timeit
def _transform_okta_user_factors(
    okta_factors: list[UserFactor],
    user_id: str,
) -> list[dict[str, Any]]:
    """
    Convert a list of Okta user factors into a format for Neo4j
    :param okta_factors: List of Okta user factors
    :param user_id: The user ID these factors belong to
    :return: List of factor dicts
    """
    transformed: list[dict[str, Any]] = []

    for factor in okta_factors:
        factor_props: dict[str, Any] = {
            "id": factor.id,
            "user_id": user_id,
            "factor_type": factor.factor_type,
            "provider": factor.provider,
            "status": factor.status,
            "created": factor.created.isoformat() if factor.created else None,
            "okta_last_updated": (
                factor.last_updated.isoformat() if factor.last_updated else None
            ),
        }
        transformed.append(factor_props)

    return transformed


@timeit
def _load_okta_user_factors(
    neo4j_session: neo4j.Session,
    factor_list: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Load Okta user factors into Neo4j
    :param neo4j_session: Session with Neo4j server
    :param factor_list: List of factor dicts to load
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    logger.info("Loading %s Okta user factors", len(factor_list))
    load(
        neo4j_session,
        OktaUserFactorSchema(),
        factor_list,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        OKTA_ORG_ID=common_job_parameters["OKTA_ORG_ID"],
    )


@timeit
def _cleanup_okta_user_factors(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale Okta user factors
    :param neo4j_session: Session with Neo4j server
    :param common_job_parameters: Settings used by all Okta modules
    :return: Nothing
    """
    logger.debug("Running cleanup for Okta user factors")
    GraphJob.from_node_schema(
        OktaUserFactorSchema(),
        common_job_parameters,
    ).run(neo4j_session)
