# Okta intel module - Organization
import logging

import neo4j

from cartography.client.core.tx import run_write_query
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
    ingest = """
    MERGE (org:OktaOrganization{id: $ORG_NAME})
    ON CREATE SET org.name = org.id, org.firstseen = timestamp()
    SET org.lastupdated = $okta_update_tag
    """

    run_write_query(
        neo4j_session,
        ingest,
        ORG_NAME=organization,
        okta_update_tag=okta_update_tag,
    )
