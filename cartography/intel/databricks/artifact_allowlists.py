import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import epoch_ms_to_datetime
from cartography.models.databricks.artifact_allowlist import (
    DatabricksArtifactAllowlistSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# One allowlist per artifact type; the API has no list endpoint so each type is
# fetched by name.
_ARTIFACT_TYPES = ("INIT_SCRIPT", "LIBRARY_JAR", "LIBRARY_MAVEN")


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: DatabricksWorkspaceClient,
    workspace_id: str,
    metastore_id: str,
    common_job_parameters: dict[str, Any],
) -> None:
    allowlists = get(api_session)
    transformed = transform(allowlists, metastore_id)
    load_artifact_allowlists(
        neo4j_session,
        transformed,
        workspace_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(api_session: DatabricksWorkspaceClient) -> list[dict[str, Any]]:
    allowlists: list[dict[str, Any]] = []
    for artifact_type in _ARTIFACT_TYPES:
        try:
            response = api_session.get(
                f"/api/2.1/unity-catalog/artifact-allowlists/{artifact_type}"
            )
        except requests.HTTPError as e:
            logger.warning(
                "Failed to fetch artifact allowlist %s: %s", artifact_type, e
            )
            continue
        response["artifact_type"] = artifact_type
        allowlists.append(response)
    return allowlists


@timeit
def transform(
    allowlists: list[dict[str, Any]], metastore_id: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for a in allowlists:
        artifact_type = a["artifact_type"]
        # Flatten matchers to "MATCH_TYPE:artifact" so the allowed patterns are
        # queryable without a child node per matcher.
        artifacts = [
            f"{m.get('match_type')}:{m.get('artifact')}"
            for m in (a.get("artifact_matchers") or [])
        ]
        result.append(
            {
                "id": f"{metastore_id}/{artifact_type}",
                "artifact_type": artifact_type,
                "metastore_id": metastore_id,
                "artifacts": artifacts,
                "created_at": epoch_ms_to_datetime(a.get("created_at")),
                "created_by": a.get("created_by"),
            }
        )
    return result


@timeit
def load_artifact_allowlists(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    workspace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DatabricksArtifactAllowlistSchema(),
        data,
        lastupdated=update_tag,
        WORKSPACE_ID=workspace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        DatabricksArtifactAllowlistSchema(), common_job_parameters
    ).run(neo4j_session)
