import logging
from typing import Any
from typing import Dict

import neo4j

from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.models.gcp.crm.folders import GCPFolderSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def _folder_resource_names(excluded_folder_ids: set[str]) -> list[str]:
    """
    Normalize excluded folder IDs (e.g. "123456") to the full resource names
    (e.g. "folders/123456") stored on GCPFolder.id.
    """
    return sorted(
        folder_id if folder_id.startswith("folders/") else f"folders/{folder_id}"
        for folder_id in excluded_folder_ids
    )


def _project_preservation_clause(
    params: Dict[str, Any],
    excluded_folder_ids: set[str],
    exclude_org_root_projects: bool,
) -> str:
    """
    Build the WHERE predicate fragment identifying GCPProject nodes (matched as
    `n`) that sit under an excluded scope and must be left untouched by cleanup.
    """
    clauses: list[str] = []

    folder_names = _folder_resource_names(excluded_folder_ids)
    if folder_names:
        clauses.append(
            """AND NOT EXISTS {
                MATCH (n)-[:PARENT*]->(ef:GCPFolder)
                WHERE ef.id IN $EXCLUDED_FOLDER_NAMES
            }"""
        )
        params["EXCLUDED_FOLDER_NAMES"] = folder_names
    if exclude_org_root_projects:
        # parent_org is NULL for folder-attached projects, so guard explicitly:
        # NOT (NULL <> x) evaluates to NULL and would wrongly filter them out.
        clauses.append(
            "AND (n.parent_org IS NULL OR n.parent_org <> $ORG_RESOURCE_NAME)"
        )
    return "\n".join(clauses)


@timeit
def cleanup_gcp_projects_preserving_exclusions(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    excluded_folder_ids: set[str],
    exclude_org_root_projects: bool,
) -> None:
    """
    Delete stale GCPProject nodes in the given org scope while preserving data
    under excluded scopes:
    - projects attached directly to the organization root, when
      exclude_org_root_projects is enabled (they were intentionally not listed
      this run), and
    - projects anywhere under an excluded folder subtree.

    Mirrors GraphJob.from_node_schema(GCPProjectSchema(), ..., cascade_delete=True):
    stale child resources attached via RESOURCE relationships are deleted along
    with each stale project, and stale relationships of non-excluded projects
    are removed. Excluded data is left completely untouched.
    """
    update_tag = common_job_parameters["UPDATE_TAG"]
    org_resource_name = common_job_parameters["ORG_RESOURCE_NAME"]

    params: Dict[str, Any] = {
        "UPDATE_TAG": update_tag,
        "ORG_RESOURCE_NAME": org_resource_name,
    }
    preservation = _project_preservation_clause(
        params, excluded_folder_ids, exclude_org_root_projects
    )

    # Stale node cleanup with cascade, in the same shape as the
    # GraphJob-generated query: stale children attached via RESOURCE are
    # deleted together with each stale project.
    run_write_query(
        neo4j_session,
        f"""
        MATCH (n:GCPProject)<-[:RESOURCE]-(:GCPOrganization{{id: $ORG_RESOURCE_NAME}})
        WHERE n.lastupdated <> $UPDATE_TAG
        {preservation}
        WITH n
        CALL (n) {{
            OPTIONAL MATCH (n)-[:RESOURCE]->(child)
            WITH child WHERE child IS NOT NULL AND child.lastupdated <> $UPDATE_TAG
            DETACH DELETE child
        }}
        DETACH DELETE n
        """,
        **params,
    )

    # Stale relationship cleanup, applying the same preservation predicate so
    # excluded projects keep their relationships while stale rels of projects
    # that were merely processed later (e.g. cross-org migration) are removed.
    run_write_query(
        neo4j_session,
        f"""
        MATCH (n:GCPProject)<-[s:RESOURCE]-(:GCPOrganization{{id: $ORG_RESOURCE_NAME}})
        WHERE s.lastupdated <> $UPDATE_TAG
        {preservation}
        DELETE s
        """,
        **params,
    )
    run_write_query(
        neo4j_session,
        f"""
        MATCH (n:GCPProject)<-[:RESOURCE]-(:GCPOrganization{{id: $ORG_RESOURCE_NAME}})
        WITH n
        MATCH (n)-[r:PARENT]->()
        WHERE r.lastupdated <> $UPDATE_TAG
        {preservation}
        DELETE r
        """,
        **params,
    )


@timeit
def cleanup_gcp_folders_preserving_exclusions(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
    excluded_folder_ids: set[str],
) -> None:
    """
    Delete stale GCPFolder nodes in the given org scope while preserving
    excluded folders and their entire subtrees.

    Falls back to the standard GraphJob cleanup when no folder exclusions are
    configured (org-root project exclusion does not affect folders).
    """
    folder_names = _folder_resource_names(excluded_folder_ids)
    if not folder_names:
        GraphJob.from_node_schema(
            GCPFolderSchema(), common_job_parameters, cascade_delete=True
        ).run(neo4j_session)
        return

    update_tag = common_job_parameters["UPDATE_TAG"]
    org_resource_name = common_job_parameters["ORG_RESOURCE_NAME"]
    params: Dict[str, Any] = {
        "UPDATE_TAG": update_tag,
        "ORG_RESOURCE_NAME": org_resource_name,
        "EXCLUDED_FOLDER_NAMES": folder_names,
    }
    preservation = """AND NOT (n.id IN $EXCLUDED_FOLDER_NAMES)
        AND NOT EXISTS {
            MATCH (n)-[:PARENT*]->(ef:GCPFolder)
            WHERE ef.id IN $EXCLUDED_FOLDER_NAMES
        }"""

    # Folders own no children via RESOURCE, so no cascade subquery is needed;
    # DETACH DELETE still removes their PARENT/RESOURCE relationships.
    run_write_query(
        neo4j_session,
        f"""
        MATCH (n:GCPFolder)<-[:RESOURCE]-(:GCPOrganization{{id: $ORG_RESOURCE_NAME}})
        WHERE n.lastupdated <> $UPDATE_TAG
        {preservation}
        DETACH DELETE n
        """,
        **params,
    )

    run_write_query(
        neo4j_session,
        f"""
        MATCH (n:GCPFolder)<-[s:RESOURCE]-(:GCPOrganization{{id: $ORG_RESOURCE_NAME}})
        WHERE s.lastupdated <> $UPDATE_TAG
        {preservation}
        DELETE s
        """,
        **params,
    )
    run_write_query(
        neo4j_session,
        f"""
        MATCH (n:GCPFolder)<-[:RESOURCE]-(:GCPOrganization{{id: $ORG_RESOURCE_NAME}})
        WITH n
        MATCH (n)-[r:PARENT]->()
        WHERE r.lastupdated <> $UPDATE_TAG
        {preservation}
        DELETE r
        """,
        **params,
    )
