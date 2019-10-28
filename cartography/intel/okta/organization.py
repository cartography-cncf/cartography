# Okta intel module - Organization
import logging

logger = logging.getLogger(__name__)


def create_okta_organization(neo4j_session, organization, okta_update_tag):
    """
    Create Okta organization in the graph
    :param neo4_session: session with the Neo4j server
    :param organization: okta organization id
    :param okta_update_tag: The timestamp value to set our new Neo4j resources with
    :return: Nothing
    """
    ingest = """
    MERGE (org:OktaOrganization{id: {ORG_NAME}})
    ON CREATE SET org.name = org.id, org.firstseen = timestamp()
    SET org.lastupdated = {okta_update_tag}
    """

    neo4j_session.run(
        ingest,
        ORG_NAME=organization,
        okta_update_tag=okta_update_tag,
    )
