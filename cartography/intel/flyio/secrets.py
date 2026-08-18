import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import get_json
from cartography.models.flyio.secret import FlySecretSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    response = get(
        api_session,
        common_job_parameters["BASE_URL"],
        common_job_parameters["APP_NAME"],
    )
    secrets = transform(response, common_job_parameters["APP_ID"])
    load_secrets(
        neo4j_session,
        secrets,
        common_job_parameters["APP_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return secrets


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    app_name: str,
) -> dict[str, Any]:
    return get_json(api_session, f"{base_url}/v1/apps/{app_name}/secrets")


def transform(response: dict[str, Any], app_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{app_id}/{secret['name']}",
            "name": secret["name"],
            "digest": secret.get("digest"),
            "created_at": secret.get("created_at"),
            "updated_at": secret.get("updated_at"),
        }
        for secret in response["secrets"]
    ]


@timeit
def load_secrets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    app_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlySecretSchema(),
        data,
        lastupdated=update_tag,
        APP_ID=app_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FlySecretSchema(), common_job_parameters).run(
        neo4j_session,
    )
