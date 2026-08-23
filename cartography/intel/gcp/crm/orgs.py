import logging
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud import resourcemanager_v3

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.models.gcp.crm.organizations import GCPOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_organizations(
    credentials: Optional[GoogleCredentials] = None,
    excluded_org_ids: Optional[set[str]] = None,
) -> List[Dict]:
    """
    Return list of GCP organizations that the authenticated principal can access using the high-level client.
    Returns empty list on error.
    :param credentials: GCP credentials.
    :param excluded_org_ids: Set of organization IDs to exclude from ingestion.
    :return: List of org dicts with keys: name, displayName, lifecycleState.
    """
    excluded = excluded_org_ids or set()
    client = resourcemanager_v3.OrganizationsClient(credentials=credentials)
    orgs = []
    for org in client.search_organizations():
        org_id = org.name.split("/")[-1]
        if org_id in excluded:
            logger.info("Excluding GCP organization %s from ingestion.", org.name)
            continue
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
    credentials: Optional[GoogleCredentials] = None,
    excluded_org_ids: Optional[set[str]] = None,
) -> List[Dict]:
    """
    Get GCP organization data using the CRM v1 resource object and load the data to Neo4j.
    Returns the list of organizations synced.
    """
    logger.debug("Syncing GCP organizations")
    data = get_gcp_organizations(
        credentials=credentials, excluded_org_ids=excluded_org_ids
    )
    load_gcp_organizations(neo4j_session, data, gcp_update_tag)
    return data


@timeit
def cleanup_excluded_gcp_organizations(
    neo4j_session: neo4j.Session,
    excluded_org_ids: set[str],
) -> None:
    """
    Delete explicitly excluded organizations and all of their resources.

    Excluded orgs are filtered out of the org loop entirely, so no per-org
    cleanup job ever runs for them. Since an exclusion means "remove this org
    from the graph", prune them here by ID. This is deliberately scoped to the
    explicitly excluded IDs rather than to stale orgs in general: an org that
    disappears due to temporary access loss (not exclusion) must keep its data.

    Descendants still reachable via RESOURCE relationships from a non-excluded
    organization are preserved — predefined GCPRole nodes (e.g. roles/viewer)
    are shared by every org and must survive the pruning of one of them.
    """
    org_names = sorted(
        org_id if org_id.startswith("organizations/") else f"organizations/{org_id}"
        for org_id in excluded_org_ids
    )
    if not org_names:
        return

    logger.info(
        "Deleting %d excluded GCP organization(s) and their resources: %s",
        len(org_names),
        ", ".join(org_names),
    )
    # All resources in an org are reachable from the org node via outgoing
    # RESOURCE relationships (org -> folders/projects/roles, project -> its
    # resources), so a variable-length traversal cascades the deletion.
    # Children still reachable from a non-excluded org (e.g. predefined
    # GCPRole nodes like roles/viewer, which are shared by every org) must be
    # preserved; only data owned solely by the excluded orgs is deleted.
    run_write_query(
        neo4j_session,
        """
        MATCH (o:GCPOrganization)
        WHERE o.id IN $ORG_NAMES
        CALL (o) {
            OPTIONAL MATCH (o)-[:RESOURCE*]->(child)
            WITH child
            WHERE child IS NOT NULL
            AND NOT EXISTS {
                MATCH (other:GCPOrganization)-[:RESOURCE*]->(child)
                WHERE NOT other.id IN $ORG_NAMES
            }
            DETACH DELETE child
        }
        DETACH DELETE o
        """,
        ORG_NAMES=org_names,
    )
