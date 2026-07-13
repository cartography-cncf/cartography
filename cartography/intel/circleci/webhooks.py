import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import paginated_get
from cartography.models.circleci.webhook import CircleCIWebhookSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    project_slug: str,
) -> None:
    project_id = common_job_parameters["PROJECT_ID"]
    raw = get(api_session, common_job_parameters["BASE_URL"], project_id)
    webhooks = transform(raw)
    load_webhooks(
        neo4j_session,
        webhooks,
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/webhook",
        params={"scope-id": project_id, "scope-type": "project"},
    )


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "name": item.get("name"),
            "url": item.get("url"),
            "verify_tls": item.get("verify_tls"),
            "has_signing_secret": bool(item.get("signing_secret")),
            "events": item.get("events"),
        }
        for item in raw
    ]


@timeit
def load_webhooks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIWebhookSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIWebhookSchema(), common_job_parameters).run(
        neo4j_session,
    )
