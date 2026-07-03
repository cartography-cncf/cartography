from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import scoped_id
from cartography.models.databricks.notebook import DatabricksNotebookSchema
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    """Materialise notebooks referenced by workloads, without a workspace walk.

    Rather than recursively listing the whole workspace tree (potentially
    thousands of files), this creates one lightweight, path-keyed
    ``DatabricksNotebook`` node per distinct notebook a job task points at, so
    the code-to-cloud ``RUNS_NOTEBOOK`` edge lands with no extra API calls. Runs
    after jobs so the task nodes it reads already exist.
    """
    paths = get_referenced_notebook_paths(neo4j_session, workspace_id)
    transformed = transform(paths, workspace_id)
    load_notebooks(
        neo4j_session, transformed, workspace_id, common_job_parameters["UPDATE_TAG"]
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_referenced_notebook_paths(
    neo4j_session: neo4j.Session, workspace_id: str
) -> list[str]:
    """Return the distinct notebook paths referenced by this workspace's tasks."""
    query = """
    MATCH (:DatabricksWorkspace {id: $workspace_id})-[:RESOURCE]->(t:DatabricksJobTask)
    WHERE t.notebook_path IS NOT NULL
    RETURN collect(DISTINCT t.notebook_path) AS paths
    """
    record = neo4j_session.run(query, workspace_id=workspace_id).single()
    return record["paths"] if record else []


@timeit
def transform(paths: list[str], workspace_id: str) -> list[dict[str, Any]]:
    return [
        {"id": scoped_id(workspace_id, path), "path": path} for path in paths if path
    ]


@timeit
def load_notebooks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksNotebookSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(DatabricksNotebookSchema(), common_job_parameters).run(
        neo4j_session
    )
