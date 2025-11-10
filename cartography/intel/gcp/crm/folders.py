import logging
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from google.auth.credentials import Credentials as GoogleCredentials
from google.cloud import resourcemanager_v3

from cartography.client.core.tx import load
from cartography.models.gcp.crm.folders import GCPFolderSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_gcp_folders(
    org_resource_name: str,
    credentials: Optional[GoogleCredentials] = None,
) -> List[Dict]:
    """
    Return a list of all descendant GCP folders under the specified organization by traversing the folder tree.

    :param org_resource_name: Full organization resource name (e.g., "organizations/123456789012")
    :return: List of folder dicts with 'name' field containing full resource names (e.g., "folders/123456")
    """
    results: List[Dict] = []
    client = resourcemanager_v3.FoldersClient(credentials=credentials)
    # BFS over folders starting at the org root
    queue: List[str] = [org_resource_name]
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


@timeit
def transform_gcp_folders(data: List[Dict]) -> List[Dict]:
    """
    Transform GCP folder data to add parent_org or parent_folder fields based on parent type.

    :param data: List of folder dicts
    :return: List of transformed folder dicts with parent_org and parent_folder fields
    """
    for folder in data:
        folder["parent_org"] = None
        folder["parent_folder"] = None

        if folder["parent"].startswith("organizations"):
            folder["parent_org"] = folder["parent"]
        elif folder["parent"].startswith("folders"):
            folder["parent_folder"] = folder["parent"]
        else:
            logger.warning(
                f"Folder {folder['name']} has unexpected parent type: {folder['parent']}"
            )

    return data


@timeit
def load_gcp_folders(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    gcp_update_tag: int,
    org_resource_name: str,
) -> None:
    """
    Load GCP folders into the graph.
    :param org_resource_name: Full organization resource name (e.g., "organizations/123456789012")
    """
    transformed_data = transform_gcp_folders(data)
    load(
        neo4j_session,
        GCPFolderSchema(),
        transformed_data,
        lastupdated=gcp_update_tag,
        ORG_RESOURCE_NAME=org_resource_name,
    )


@timeit
def sync_gcp_folders(
    neo4j_session: neo4j.Session,
    gcp_update_tag: int,
    common_job_parameters: Dict,
    org_resource_name: str,
    credentials: Optional[GoogleCredentials] = None,
) -> List[Dict]:
    """
    Get GCP folder data using the CRM v2 resource object and load the data to Neo4j.
    :param org_resource_name: Full organization resource name (e.g., "organizations/123456789012")
    :return: List of folders synced
    """
    logger.debug("Syncing GCP folders")
    folders = get_gcp_folders(org_resource_name, credentials=credentials)
    load_gcp_folders(neo4j_session, folders, gcp_update_tag, org_resource_name)
    return folders
