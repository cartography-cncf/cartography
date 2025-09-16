import logging
from typing import Dict
from typing import List

import neo4j
from google.cloud import resourcemanager_v3

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.gcp.crm.folders import GCPFolderSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_folders(org_id: str) -> List[Dict]:
    """
    Return a list of all descendant GCP folders under the specified organization by traversing the folder tree.

    :param org_id: Numeric organization id, e.g., "123456789012".
    :return: List of folder dicts.
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
    # Transform data to set parent_org or parent_folder based on parent type
    transformed_data = []
    for folder in data:
        transformed_folder = {
            "name": folder["name"],
            "displayName": folder.get("displayName"),
            "lifecycleState": folder.get("lifecycleState"),
            "parent_org": None,
            "parent_folder": None,
        }

        if folder["parent"].startswith("organizations"):
            transformed_folder["parent_org"] = folder["parent"]
        elif folder["parent"].startswith("folders"):
            transformed_folder["parent_folder"] = folder["parent"]
        else:
            logger.warning(
                f"Skipping folder {folder['name']} with unexpected parent type: {folder['parent']}"
            )
            continue

        transformed_data.append(transformed_folder)

    load(
        neo4j_session,
        GCPFolderSchema(),
        transformed_data,
        lastupdated=gcp_update_tag,
        ORG_ID=f"organizations/{org_id}",
    )


@timeit
def sync_gcp_folders(
    neo4j_session: neo4j.Session,
    gcp_update_tag: int,
    common_job_parameters: Dict,
    org_id: str,
    defer_cleanup: bool = False,
) -> List[Dict]:
    """
    Get GCP folder data using the CRM v2 resource object, load the data to Neo4j, and clean up stale nodes.
    Returns the list of folders synced.
    :param defer_cleanup: If True, skip the cleanup job. Used for hierarchical cleanup scenarios.
    """
    logger.debug("Syncing GCP folders")
    folders = get_gcp_folders(org_id)
    load_gcp_folders(neo4j_session, folders, gcp_update_tag, org_id)
    if not defer_cleanup:
        GraphJob.from_node_schema(GCPFolderSchema(), common_job_parameters).run(
            neo4j_session
        )
    return folders
