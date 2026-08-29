"""Snowflake image repositories and the images they hold.

Image repositories are listed per schema, and the images in each repository come from a
second listing per repository. The images are what a service container's HAS_IMAGE edge
resolves against, matched on the untagged registry path plus the digest, which is what
turns "a container is running" into "this exact image, from this repository, pushed on
this date, is running".

``get`` returns one bundle per repository, pairing the raw repository payload with the
schema it was found in and with its own image listing, so ``transform`` can key each
image on its repository without re-deriving anything.
"""

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
from cartography.intel.snowflake.util import untag_image_path
from cartography.models.snowflake.image_repository import SnowflakeImageRepositorySchema
from cartography.models.snowflake.image_repository import SnowflakeImageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_image_repositories(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Image repositories of one schema, or None when the schema is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}"
            "/image-repositories",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list image repositories of Snowflake schema %s.%s (permission "
            "denied); they will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get_repository_images(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
    repository_name: str,
) -> list[dict[str, Any]] | None:
    """Images of one repository, or None when the repository is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}"
            f"/image-repositories/{sf_path_segment(repository_name)}/images",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list images of Snowflake image repository %s.%s.%s (permission "
            "denied); they will be missing from the graph.",
            database_name,
            schema_name,
            repository_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return one bundle per readable repository plus whether everything was read."""
    bundles: list[dict[str, Any]] = []
    complete = True

    for schema in schemas:
        database_name = schema["database_name"]
        schema_name = schema["name"]
        repositories = get_schema_image_repositories(client, database_name, schema_name)
        if repositories is None:
            complete = False
            continue

        for repository in repositories:
            images = get_repository_images(
                client, database_name, schema_name, repository["name"]
            )
            if images is None:
                complete = False
            bundles.append(
                {
                    "database_name": database_name,
                    "schema_name": schema_name,
                    "repository": repository,
                    "images": images or [],
                },
            )
    return bundles, complete


def transform(
    bundles: list[dict[str, Any]],
    account_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return ``(image repositories, images)``.

    An image's node id carries its digest as well as its name: the same image name is
    repushed with new content over time, and keying on the name alone would collapse
    every version onto one node and lose which digest is actually deployed.
    """
    repositories: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []

    for bundle in bundles:
        database_name = bundle["database_name"]
        schema_name = bundle["schema_name"]
        repository = bundle["repository"]
        name = repository["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        repository_id = sf_id(account_id, "image_repository", qualified_name)
        repositories.append(
            {
                "id": repository_id,
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "repository_url": repository.get("repository_url"),
                "privatelink_repository_url": repository.get(
                    "privatelink_repository_url"
                ),
                "owner": repository.get("owner"),
                "comment": repository.get("comment"),
                "created_on": iso_to_datetime(repository.get("created_on")),
            },
        )

        for image in bundle["images"]:
            image_name = image["image_name"]
            digest = image["digest"]
            images.append(
                {
                    "id": sf_id(
                        account_id,
                        "image",
                        f"{qualified_name}.{sf_fqn(image_name)}@{digest}",
                    ),
                    "name": image_name,
                    "digest": digest,
                    "image_path": image.get("image_path"),
                    "untagged_image_path": untag_image_path(image.get("image_path")),
                    "tags": image.get("tags"),
                    "size": image.get("size"),
                    "repository_name": qualified_name,
                    "parent_repository_id": repository_id,
                    "uploaded_on": iso_to_datetime(image.get("uploaded_on")),
                },
            )

    return repositories, images


def load_image_repositories(
    neo4j_session: neo4j.Session,
    repositories: list[dict[str, Any]],
    images: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeImageRepositorySchema(),
        repositories,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )
    load(
        neo4j_session,
        SnowflakeImageSchema(),
        images,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeImageSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        SnowflakeImageRepositorySchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync Snowflake image repositories and their images.

    Runs before services so a container's HAS_IMAGE edge resolves against an image node
    already in the graph. Returns whether every schema and repository could be read.
    """
    bundles, complete = get(client, schemas)
    repositories, images = transform(bundles, client.account_id)
    logger.info(
        "Loading %d Snowflake image repositories and %d images for account %s.",
        len(repositories),
        len(images),
        client.account_id,
    )
    load_image_repositories(
        neo4j_session,
        repositories,
        images,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    if not complete:
        logger.warning(
            "Some Snowflake image repositories could not be listed; skipping cleanup so "
            "still-valid repositories and images are not deleted.",
        )
    return complete
