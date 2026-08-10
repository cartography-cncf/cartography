import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import paginated_get
from cartography.intel.circleci.util import parse_iso
from cartography.models.circleci.context_env_var import CircleCIContextEnvVarSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_id: str,
    contexts: list[dict[str, Any]],
) -> None:
    env_vars: list[dict[str, Any]] = []
    for context in contexts:
        raw = get(api_session, common_job_parameters["BASE_URL"], context["id"])
        env_vars.extend(transform(raw, context["id"]))
    load_context_env_vars(
        neo4j_session,
        env_vars,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    # Cleanup once per org, after every context's variables are loaded, so an
    # early context's cleanup cannot delete a later context's freshly-loaded vars.
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    context_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/context/{context_id}/environment-variable",
    )


def transform(
    raw: list[dict[str, Any]],
    context_id: str,
) -> list[dict[str, Any]]:
    # The API never returns secret values, only the variable name + metadata.
    return [
        {
            "id": f"{context_id}:{item['variable']}",
            "variable": item["variable"],
            "context_id": context_id,
            "created_at": parse_iso(item.get("created_at")),
            "updated_at": parse_iso(item.get("updated_at")),
        }
        for item in raw
    ]


@timeit
def load_context_env_vars(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIContextEnvVarSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIContextEnvVarSchema(), common_job_parameters).run(
        neo4j_session
    )
