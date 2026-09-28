"""Snowflake artifact repositories: schema-level proxies to external package indexes."""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.artifact_repository import (
    SnowflakeArtifactRepositorySchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Artifact repositories in one schema, or None when the schema is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}"
            "/artifact-repositories",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def transform(
    repositories: list[dict[str, Any]],
    schema: dict[str, Any],
    account_id: str,
) -> list[dict[str, Any]]:
    database_name = schema["database_name"]
    schema_name = schema["name"]
    transformed: list[dict[str, Any]] = []

    for repository in repositories:
        name = repository["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        api_integration = repository.get("api_integration")
        transformed.append(
            {
                "id": sf_id(account_id, "artifact_repository", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": schema["id"],
                "repository_type": repository.get("repository_type"),
                "api_integration": api_integration,
                "api_integration_id": (
                    sf_id(account_id, "api_integration", sf_fqn(api_integration))
                    if api_integration
                    else None
                ),
                "owner": repository.get("owner"),
                "comment": repository.get("comment"),
                "created_on": iso_to_datetime(repository.get("created_on")),
            },
        )
    return transformed


def load_artifact_repositories(
    neo4j_session: neo4j.Session,
    repositories: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeArtifactRepositorySchema(),
        repositories,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeArtifactRepositorySchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync every artifact repository in every readable schema.

    Returns whether the walk was complete, so the caller can skip cleanup rather
    than deleting nodes it merely failed to re-read this run.
    """
    account_id = client.account_id
    repositories: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        listing = get(client, schema["database_name"], schema["name"])
        if listing is None:
            complete = False
            continue
        repositories.extend(transform(listing, schema, account_id))

    logger.info(
        "Loading %d Snowflake artifact repositories for account %s.",
        len(repositories),
        account_id,
    )
    load_artifact_repositories(
        neo4j_session, repositories, account_id, common_job_parameters["UPDATE_TAG"]
    )

    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be read for artifact repositories; "
            "skipping their cleanup so still-valid nodes are not deleted.",
        )
    return complete
