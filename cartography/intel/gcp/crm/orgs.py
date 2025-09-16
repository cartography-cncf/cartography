import logging
from typing import Dict
from typing import List

import neo4j
from google.cloud import resourcemanager_v3

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.crm.organizations import GCPOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_organizations() -> List[Dict]:
    """
    Return list of GCP organizations that the authenticated principal can access using the high-level client.
    Returns empty list on error.
    :return: List of org dicts with keys: name, displayName, lifecycleState.
    """
    client = resourcemanager_v3.OrganizationsClient()
    try:
        orgs = []
        for org in client.search_organizations():
            orgs.append(
                {
                    "name": org.name,
                    "displayName": org.display_name,
                    "lifecycleState": org.state.name,
                }
            )
        return orgs
    except Exception as e:
        logger.warning(
            "Exception occurred in crm.get_gcp_organizations(), returning empty list. Details: %r",
            e,
        )
        return []


@timeit
def load_gcp_organizations(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
) -> None:
    # Add id field if not present (for compatibility with test data)
    transformed_data = []
    for org in data:
        org_copy = org.copy()
        if "id" not in org_copy:
            org_copy["id"] = org_copy["name"]
        transformed_data.append(org_copy)

    load(
        neo4j_session,
        GCPOrganizationSchema(),
        transformed_data,
        lastupdated=gcp_update_tag,
    )


@timeit
def sync_gcp_organizations(
    neo4j_session: neo4j.Session,
    gcp_update_tag: int,
    common_job_parameters: Dict,
    defer_cleanup: bool = False,
) -> List[Dict]:
    """
    Get GCP organization data using the CRM v1 resource object, load the data to Neo4j, and clean up stale nodes.
    Returns the list of organizations synced.
    :param defer_cleanup: If True, skip the cleanup job. Used for hierarchical cleanup scenarios.
    """
    logger.debug("Syncing GCP organizations")
    data = get_gcp_organizations()
    load_gcp_organizations(neo4j_session, data, gcp_update_tag)
    if not defer_cleanup:
        GraphJob.from_node_schema(GCPOrganizationSchema(), common_job_parameters).run(
            neo4j_session
        )
    return data
