import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.unikraft.util import list_resources
from cartography.intel.unikraft.util import METRO_BASE_URLS
from cartography.intel.unikraft.util import require_non_empty
from cartography.models.unikraft.image import UnikraftImageSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, base_url: str) -> list[dict[str, Any]]:
    return list_resources(
        session, f"{base_url}/v1/images", "images", cursor_field="url"
    )


def transform(images: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "url": require_non_empty(image.get("url"), "image url"),
            "created_at": image.get("created_at"),
            "initrd_or_rom": image.get("initrd_or_rom"),
            "size_in_bytes": image.get("size_in_bytes"),
            "tags": image.get("tags"),
        }
        for image in images
    ]


@timeit
def load_images(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    account_id: str,
    metro: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        UnikraftImageSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
        METRO=metro,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(UnikraftImageSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for metro, base_url in METRO_BASE_URLS.items():
        images = get(session, base_url)
        transformed = transform(images)
        load_images(neo4j_session, transformed, account_id, metro, update_tag)
    cleanup(neo4j_session, common_job_parameters)
