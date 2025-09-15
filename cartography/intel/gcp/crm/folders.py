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
def get_gcp_folders(crm_v2: Resource) -> List[Dict]:
    """
    Return list of GCP folders that the crm_v2 resource object has permissions to access.
    Returns empty list if we are unable to enumerate folders for any reason.
    :param crm_v2: The Resource Manager v2 resource object.
    :return: List of GCP folders.
    """
    try:
        req = crm_v2.folders().search(body={})
        res = req.execute()
        return res.get("folders", [])
    except HttpError as e:
        logger.warning(
            "HttpError occurred in crm.get_gcp_folders(), returning empty list. Details: %r",
            e,
        )
        return []


@timeit
def load_gcp_folders(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
) -> None:
    """
    Ingest the GCP folders to Neo4j.
    """
    for folder in data:
        if folder["parent"].startswith("organizations"):
            query = "MATCH (parent:GCPOrganization{id:$ParentId})"
        elif folder["parent"].startswith("folders"):
            query = """
            MERGE (parent:GCPFolder{id:$ParentId})
            ON CREATE SET parent.firstseen = timestamp()
            """
        else:
            # Skip folders with unexpected parent types
            logger.warning(
                f"Skipping folder {folder['name']} with unexpected parent type: {folder['parent']}"
            )
            continue
        query += """
        MERGE (folder:GCPFolder{id:$FolderName})
        ON CREATE SET folder.firstseen = timestamp()
        SET folder.foldername = $FolderName,
            folder.displayname = $DisplayName,
            folder.lifecyclestate = $LifecycleState,
            folder.lastupdated = $gcp_update_tag
        WITH parent, folder
        MERGE (parent)-[r:RESOURCE]->(folder)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $gcp_update_tag
        """
        neo4j_session.run(
            query,
            ParentId=folder["parent"],
            FolderName=folder["name"],
            DisplayName=folder.get("displayName", None),
            LifecycleState=folder.get("lifecycleState", None),
            gcp_update_tag=gcp_update_tag,
        )


@timeit
def cleanup_gcp_folders(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale GCP folders and their relationships.
    """
    run_cleanup_job("gcp_crm_folder_cleanup.json", neo4j_session, common_job_parameters)


@timeit
def sync_gcp_folders(
    neo4j_session: neo4j.Session,
    crm_v2: Resource,
    gcp_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Get GCP folder data using the CRM v2 resource object, load the data to Neo4j, and clean up stale nodes.
    """
    logger.debug("Syncing GCP folders")
    folders = get_gcp_folders(crm_v2)
    load_gcp_folders(neo4j_session, folders, gcp_update_tag)
    cleanup_gcp_folders(neo4j_session, common_job_parameters)
