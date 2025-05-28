import logging

import neo4j

import cartography.intel.airbyte.organizations

import cartography.intel.airbyte.users
# import cartography.intel.airbyte.sources
# import cartography.intel.airbyte.destinations
# import cartography.intel.airbyte.connections
# import cartography.intel.airbyte.workspaces
from cartography.config import Config
from cartography.intel.airbyte.util import AirbyteClient
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_airbyte_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    If this module is configured, perform ingestion of Airbyte data. Otherwise warn and exit
    :param neo4j_session: Neo4J session for database interface
    :param config: A cartography.config object
    :return: None
    """
    if not config.airbyte_client_id or not config.airbyte_client_secret:
        logger.info(
            "Airbyte import is not configured - skipping this module. "
            "See docs to configure.",
        )
        return

    # Create api session
    api_client = AirbyteClient(
        base_url=config.airbyte_api_url,
        client_id=config.airbyte_client_id,
        client_secret=config.airbyte_client_secret,
    )

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    for organization in cartography.intel.airbyte.organizations.sync(
        neo4j_session,
        api_client,
        common_job_parameters,
    ):
        org_common_job_parameters = {
            "UPDATE_TAG": config.update_tag,
            "ORG_ID": organization["organizationId"],
        }
        cartography.intel.airbyte.users.sync(
            neo4j_session,
            api_client,
            organization["organizationId"],
            org_common_job_parameters,
        )

        # WIP: https://reference.airbyte.com/reference/listapplications
        # WIP: https://reference.airbyte.com/reference/listtags

        """


        cartography.intel.airbyte.sources.sync(
            neo4j_session,
            api_session,
            org_common_job_parameters,
            sourceId=config.airbyte_sourceid,
        )

        cartography.intel.airbyte.destinations.sync(
            neo4j_session,
            api_session,
            org_common_job_parameters,
            destinationId=config.airbyte_destinationid,
        )

        cartography.intel.airbyte.connections.sync(
            neo4j_session,
            api_session,
            org_common_job_parameters,
            connectionId=config.airbyte_connectionid,
        )

        cartography.intel.airbyte.workspaces.sync(
            neo4j_session,
            api_session,
            org_common_job_parameters,
            workspaceId=config.airbyte_workspaceid,
        )
        """
