import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import paginated_get
from cartography.intel.circleci.util import parse_iso
from cartography.models.circleci.context import CircleCIContextSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_id: str,
) -> list[dict[str, Any]]:
    raw = get(api_session, common_job_parameters["BASE_URL"], org_id)
    contexts = transform(raw)
    load_contexts(
        neo4j_session,
        contexts,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return contexts


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/context",
        params={"owner-id": org_id, "owner-type": "organization"},
    )


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": ctx["id"],
            "name": ctx.get("name"),
            "created_at": parse_iso(ctx.get("created_at")),
        }
        for ctx in raw
    ]


@timeit
def load_contexts(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIContextSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIContextSchema(), common_job_parameters).run(
        neo4j_session,
    )
