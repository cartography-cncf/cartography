import logging
from typing import Dict
from typing import List

import neo4j
from google.cloud import resourcemanager_v3

from cartography.client.core.tx import load
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


@timeit
def load_gcp_organizations(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
) -> None:
    for org in data:
        org["id"] = org["name"]

    load(
        neo4j_session,
        GCPOrganizationSchema(),
        data,
        lastupdated=gcp_update_tag,
    )


@timeit
def sync_gcp_organizations(
    neo4j_session: neo4j.Session,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> List[Dict]:
    """
    Get GCP organization data using the CRM v1 resource object and load the data to Neo4j.
    Returns the list of organizations synced.
    """
    logger.debug("Syncing GCP organizations")
    data = get_gcp_organizations()
    load_gcp_organizations(neo4j_session, data, gcp_update_tag)
    return data
