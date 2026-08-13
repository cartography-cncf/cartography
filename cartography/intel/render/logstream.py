import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.models.render.logstream import RenderLogStreamSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> dict[str, Any] | None:
    """
    :return: The workspace's log stream config, or None if it has none configured
        (Render returns 404 for a workspace with no log stream set up).
    """
    response = session.get(
        f"{BASE_URL}/logs/streams/owner/{owner_id}", timeout=(60, 60)
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict):
        raise ValueError(
            f"Render API returned a non-object log stream response for owner "
            f"{owner_id}: {type(body)}."
        )
    return body


def transform(log_stream: dict[str, Any] | None, owner_id: str) -> list[dict[str, Any]]:
    if log_stream is None:
        return []
    return [
        {
            "ownerId": owner_id,
            "endpoint": log_stream.get("endpoint"),
            "preview": log_stream.get("preview"),
        }
    ]


@timeit
def load_log_stream(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderLogStreamSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderLogStreamSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    log_stream = get(session, owner_id)
    transformed = transform(log_stream, owner_id)
    load_log_stream(neo4j_session, transformed, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
