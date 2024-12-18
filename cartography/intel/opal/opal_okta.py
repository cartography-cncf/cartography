import logging

import neo4j

from cartography.client.core.tx import load
from cartography.intel.opal.opal_common import load_auto_approved_access
from cartography.intel.opal.opal_common import load_manual_approvers
from cartography.intel.opal.opal_common import parse_opal_resource_access_configuration
from cartography.models.opal.opalresource import OpalResourceSchema
logger = logging.getLogger(__name__)

PAGE_SIZE = 200


def load_opal_groups_as_resources(neo4j_session: neo4j.Session, groups: list[dict], update_tag: int) -> None:
    """
    Load Opal resources into the Neo4j database.

    :param neo4j_session: The Neo4j session to use for loading data.
    :param resources: The resources to load.
    :param update_tag: The update tag to use for the load operation.
    """
    logger.info(f"Loaded {len(groups)} opal aws resources")
    load(neo4j_session, OpalResourceSchema(), groups, lastupdated=update_tag)


def sync_opal_okta(
    neo4j_session: neo4j.Session,
    update_tag: int,
    groups: list[dict],
    opal_to_okta_map: dict,
    owner_ids_to_okta_groups_map: dict,
) -> None:
    """
    Sync Opal resources into Cartography.
    """

    load_opal_groups_as_resources(neo4j_session, groups, update_tag)
    auto_approved_access, manual_approved_access = parse_opal_resource_access_configuration(
        groups, opal_to_okta_map, owner_ids_to_okta_groups_map,
    )
    load_auto_approved_access(neo4j_session, update_tag, auto_approved_access)
    load_manual_approvers(neo4j_session, update_tag, manual_approved_access)
