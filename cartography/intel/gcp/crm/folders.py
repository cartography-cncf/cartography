import logging
from typing import Dict
from typing import List

import neo4j
from google.cloud import resourcemanager_v3

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_folders(org_id: str) -> List[Dict]:
    """
    Return a list of all descendant GCP folders under the specified organization by traversing the folder tree.
    Uses Cloud Resource Manager v2 folders.list with recursion.

    :param crm_v2: The Resource Manager v2 discovery client.
    :param org_id: Numeric organization id, e.g., "123456789012".
    :return: List of folder dicts as returned by v2.
    """
    results: List[Dict] = []
    client = resourcemanager_v3.FoldersClient()
    try:
        # BFS over folders starting at the org root
        queue: List[str] = [f"organizations/{org_id}"]
        seen: set[str] = set()
        while queue:
            parent = queue.pop(0)
            if parent in seen:
                continue
            seen.add(parent)

            for folder in client.list_folders(parent=parent):
                results.append(
                    {
                        "name": folder.name,
                        "parent": parent,
                        "displayName": folder.display_name,
                        "lifecycleState": folder.state.name,
                    }
                )
                if folder.name:
                    queue.append(folder.name)
        return results
    except Exception as e:
        logger.warning(
            "Exception occurred in crm.get_gcp_folders(), returning empty list. Details: %r",
            e,
        )
        return []


@timeit
def load_gcp_folders(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
    org_id: str,
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
        MERGE (parent)-[r:PARENT]->(folder)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $gcp_update_tag
        WITH folder
        MATCH (org:GCPOrganization{id:$OrgName})
        MERGE (org)-[r2:RESOURCE]->(folder)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $gcp_update_tag
        """
        neo4j_session.run(
            query,
            ParentId=folder["parent"],
            FolderName=folder["name"],
            DisplayName=folder.get("displayName", None),
            LifecycleState=folder.get("lifecycleState", None),
            OrgName=f"organizations/{org_id}",
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
    gcp_update_tag: int,
    common_job_parameters: Dict,
    org_id: str,
) -> None:
    """
    Get GCP folder data using the CRM v2 resource object, load the data to Neo4j, and clean up stale nodes.
    """
    logger.debug("Syncing GCP folders")
    folders = get_gcp_folders(org_id)
    load_gcp_folders(neo4j_session, folders, gcp_update_tag, org_id)
    cleanup_gcp_folders(neo4j_session, common_job_parameters)
