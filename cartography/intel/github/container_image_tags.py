"""
GitHub Container Image Tags Intelligence Module.

Loads ``GitHubContainerImageTag`` nodes that point each (package, tag-name)
pair at its image digest. Tag rows are produced by
``cartography.intel.github.container_images.sync_container_images`` while it
walks per-package versions, since that is where the package context is in
scope. This module is responsible for loading and cleanup only.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.github.container_image_tags import GitHubContainerImageTagSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def load_container_image_tags(
    neo4j_session: neo4j.Session,
    tags: list[dict[str, Any]],
    org_url: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        GitHubContainerImageTagSchema(),
        tags,
        lastupdated=update_tag,
        org_url=org_url,
    )


@timeit
def cleanup_container_image_tags(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        GitHubContainerImageTagSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_container_image_tags(
    neo4j_session: neo4j.Session,
    organization: str,
    tag_rows: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    org_url = f"https://github.com/{organization}"
    if tag_rows:
        logger.info(
            "Loading %d GHCR tag nodes for %s",
            len(tag_rows),
            organization,
        )
        load_container_image_tags(neo4j_session, tag_rows, org_url, update_tag)
    cleanup_params = dict(common_job_parameters)
    cleanup_params["org_url"] = org_url
    cleanup_container_image_tags(neo4j_session, cleanup_params)
