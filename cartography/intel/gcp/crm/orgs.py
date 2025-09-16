import logging
from typing import Dict
from typing import List

import neo4j
from googleapiclient.discovery import HttpError
from googleapiclient.discovery import Resource

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_organizations(crm_v1: Resource) -> List[Dict]:
    """
    Return list of GCP organizations that the crm_v1 resource object has permissions to access.
    Returns empty list if we are unable to enumerate organizations for any reason.
    :param crm_v1: The Compute Resource Manager v1 resource object created by `googleapiclient.discovery.build()`.
    :return: List of GCP Organizations.
    """
    try:
        req = crm_v1.organizations().search(body={})
        res = req.execute()
        return res.get("organizations", [])
    except HttpError as e:
        logger.warning(
            "HttpError occurred in crm.get_gcp_organizations(), returning empty list. Details: %r",
            e,
        )
        return []


@timeit
def load_gcp_organizations(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
) -> None:
    """
    Ingest the GCP organizations to Neo4j.
    """
    query = """
    MERGE (org:GCPOrganization{id:$OrgName})
    ON CREATE SET org.firstseen = timestamp()
    SET org.orgname = $OrgName,
        org.displayname = $DisplayName,
        org.lifecyclestate = $LifecycleState,
        org.lastupdated = $gcp_update_tag
    """
    for org_object in data:
        neo4j_session.run(
            query,
            OrgName=org_object["name"],
            DisplayName=org_object.get("displayName", None),
            LifecycleState=org_object.get("lifecycleState", None),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def cleanup_gcp_organizations(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale GCP organizations and their relationships.
    """
    run_cleanup_job(
        "gcp_crm_organization_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_gcp_organizations(
    neo4j_session: neo4j.Session,
    crm_v1: Resource,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP organization data using the CRM v1 resource object, load the data to Neo4j, and clean up stale nodes.
    """
    logger.debug("Syncing GCP organizations")
    data = get_gcp_organizations(crm_v1)
    load_gcp_organizations(neo4j_session, data, gcp_update_tag)
    cleanup_gcp_organizations(neo4j_session, common_job_parameters)
