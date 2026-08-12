import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.secretfile import RenderSecretFileSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, service_id: str) -> list[dict[str, Any]]:
    # Render's response includes each secret file's full plaintext `content`
    # alongside its `name`. transform() below discards `content` immediately and it
    # is never logged, stored, or passed to load() - only the name is ingested.
    return list_paginated(
        session,
        f"{BASE_URL}/services/{service_id}/secret-files",
        "secretFile",
    )


def transform(
    secret_files: list[dict[str, Any]],
    service_id: str,
    owner_id: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{service_id}/{require_non_empty(secret_file.get('name'), 'secret file name')}",
            "name": secret_file.get("name"),
            "ownerId": owner_id,
            "serviceId": service_id,
        }
        for secret_file in secret_files
    ]


@timeit
def load_secret_files(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderSecretFileSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderSecretFileSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    service_ids: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    all_secret_files: list[dict[str, Any]] = []
    for service_id in service_ids:
        secret_files = get(session, service_id)
        all_secret_files.extend(transform(secret_files, service_id, owner_id))
    load_secret_files(neo4j_session, all_secret_files, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
