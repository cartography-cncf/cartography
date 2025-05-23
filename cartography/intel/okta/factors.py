# Okta intel module - Factors
import logging
from typing import Dict
from typing import List
from typing import Any

import neo4j
from okta import FactorsClient
from okta.framework.OktaError import OktaError
from okta.models.factor.Factor import Factor

from cartography.client.core.tx import load
from cartography.models.okta.userfactor import OktaUserFactorSchema
from cartography.intel.okta.sync_state import OktaSyncState
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def _create_factor_client(okta_org: str, okta_api_key: str) -> FactorsClient:
    """
    Create Okta FactorsClient
    :param okta_org: Okta organization name
    :param okta_api_key: Okta API Key
    :return: Instance of FactorsClient
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/FactorsClient.py
    factor_client = FactorsClient(
        base_url=f"https://{okta_org}.okta.com/",
        api_token=okta_api_key,
    )

    return factor_client


@timeit
def _get_factor_for_user_id(factor_client: FactorsClient, user_id: str) -> List[Factor]:
    """
    Get factor for user from the Okta server
    :param factor_client: factor client
    :param user_id: user to fetch the data from
    :return: Array of user factor information
    """

    try:
        factor_results = factor_client.get_lifecycle_factors(user_id)
    except OktaError as okta_error:
        logger.debug(
            f"Unable to get factor for user id {user_id} with "
            f"error code {okta_error.error_code} with description {okta_error.error_summary}",
        )

        return []

    return factor_results


@timeit
def transform_okta_user_factor_list(okta_factor_list: List[Factor], user_id: str) -> List[Dict]:
    factors = []

    for current in okta_factor_list:
        transformed_factor = transform_okta_user_factor(current)
        transformed_factor["user_id"] = user_id
        factors.append(transformed_factor)

    return factors


@timeit
def transform_okta_user_factor(okta_factor_info: Factor) -> Dict:
    """
    Transform okta user factor into consumable data for the graph
    :param okta_factor_info: okta factor information
    :return: Dictionary of properties for the factor
    """

    # https://github.com/okta/okta-sdk-python/blob/master/okta/models/factor/Factor.py
    factor_props = {}
    factor_props["id"] = okta_factor_info.id
    factor_props["factor_type"] = okta_factor_info.factorType
    factor_props["provider"] = okta_factor_info.provider
    factor_props["status"] = okta_factor_info.status
    if okta_factor_info.created:
        factor_props["created"] = okta_factor_info.created.strftime(
            "%m/%d/%Y, %H:%M:%S",
        )
    else:
        factor_props["created"] = None

    if okta_factor_info.lastUpdated:
        factor_props["okta_last_updated"] = okta_factor_info.lastUpdated.strftime(
            "%m/%d/%Y, %H:%M:%S",
        )
    else:
        factor_props["okta_last_updated"] = None

    # we don't import Profile data into the graph due as it contains sensitive data
    return factor_props


@timeit
def _load_user_factors(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    factors: List[Dict],
    okta_update_tag: int,
) -> None:
    """
    Add user factors into the graph
    :param neo4j_session: session with the Neo4j server
    :param user_id: user to map factors to
    :param factors: factors to add
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    load(
        neo4j_session,
        OktaUserFactorSchema(),
        factors,
        lastupdated=okta_update_tag,
        ORG_ID=okta_org_id,
    )


@timeit
def sync_users_factors(
    neo4j_session: neo4j.Session,
    okta_org_id: str,
    okta_update_tag: int,
    okta_api_key: str,
    sync_state: OktaSyncState,
) -> None:
    """
    Sync user factors
    :param neo4j_session: session with the Neo4j server
    :param okta_org_id: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :param okta_api_key: Okta API key
    :param sync_state: Okta sync state
    :return: Nothing
    """

    logger.info("Syncing Okta User Factors")

    factor_client = _create_factor_client(okta_org_id, okta_api_key)

    if sync_state.users:
        factors: list[dict[str, Any]] = []
        for user_id in sync_state.users:
            factor_data = _get_factor_for_user_id(factor_client, user_id)
            factors.extend(transform_okta_user_factor_list(factor_data, user_id))
        _load_user_factors(neo4j_session, okta_org_id, factors, okta_update_tag)
