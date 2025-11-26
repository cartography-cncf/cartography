# Okta intel module - Organization
import logging

import neo4j

from cartography.client.core.tx import load
from cartography.models.okta.organization import OktaOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def create_okta_organization(
    neo4j_session: neo4j.Session,
    organization: str,
    okta_update_tag: int,
) -> None:
    """
    Create Okta organization in the graph
    :param neo4_session: session with the Neo4j server
    :param organization: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    load(
        neo4j_session,
        OktaOrganizationSchema(),
        [{"name": organization}],
        lastupdated=okta_update_tag,
    )
