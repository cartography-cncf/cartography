import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.modal.util import list_image_tags
from cartography.intel.modal.util import ModalClient
from cartography.models.modal.image import ModalImageSchema
from cartography.models.modal.image_tag import ModalImageTagSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
async def sync(
    neo4j_session: neo4j.Session,
    client: ModalClient,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """Ingest the named images of one environment and the tags pointing at them.

    Runs before sandboxes so their HAS_IMAGE edge can resolve.
    """
    environment_name = common_job_parameters["ENVIRONMENT_NAME"]
    environment_id = common_job_parameters["ENVIRONMENT_ID"]
    update_tag = common_job_parameters["UPDATE_TAG"]

    raw = await list_image_tags(client, environment_name)

    images = transform(raw, environment_name)
    load_images(neo4j_session, images, environment_id, update_tag)

    tags = transform_tags(raw, environment_name)
    load_image_tags(neo4j_session, tags, environment_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
    return images


def transform(raw: list[dict[str, Any]], environment_name: str) -> list[dict[str, Any]]:
    """Deduplicate the per-tag listing down to one row per image.

    Modal lists tags, not images, so one image published under several tags appears several
    times. Keeping the first occurrence is enough: the fields kept here describe the image, not
    the tag.
    """
    images: dict[str, dict[str, Any]] = {}
    for row in raw:
        image_id = row["id"]
        if image_id in images:
            continue
        images[image_id] = {
            "id": image_id,
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "environment_name": environment_name,
        }
    return list(images.values())


def transform_tags(
    raw: list[dict[str, Any]], environment_name: str
) -> list[dict[str, Any]]:
    """One node per tag, so aliases of the same image are all preserved."""
    return [
        {
            # Synthesised reference, mirroring `repo_uri:tag` elsewhere. Modal exposes no
            # registry URI, so the image id stands in for the repository part.
            "id": f"{row['id']}:{row['tag']}",
            "tag": row["tag"],
            "image_id": row["id"],
            "revision_id": row.get("revision_id"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "environment_name": environment_name,
        }
        for row in raw
    ]


@timeit
def load_images(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalImageSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def load_image_tags(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    environment_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ModalImageTagSchema(),
        data,
        lastupdated=update_tag,
        ENVIRONMENT_ID=environment_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Tags before images: the tag is the child, and its IMAGE edge needs its target to still
    # exist while it is being matched.
    GraphJob.from_node_schema(ModalImageTagSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ModalImageSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_for_environment(
    neo4j_session: neo4j.Session,
    workspace_id: str,
    environment_id: str,
    update_tag: int,
) -> None:
    """Tear down this resource for one environment, by id. See `environments` for why."""
    cleanup(
        neo4j_session,
        {
            "UPDATE_TAG": update_tag,
            "WORKSPACE_ID": workspace_id,
            "ENVIRONMENT_ID": environment_id,
        },
    )
