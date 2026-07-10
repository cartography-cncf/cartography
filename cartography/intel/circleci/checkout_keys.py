import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import paginated_get
from cartography.intel.circleci.util import parse_iso
from cartography.models.circleci.checkout_key import CircleCICheckoutKeySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    project_slug: str,
) -> None:
    raw = get(api_session, common_job_parameters["BASE_URL"], project_slug)
    keys = transform(raw, project_slug)
    load_checkout_keys(
        neo4j_session,
        keys,
        common_job_parameters["PROJECT_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_slug: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/project/{project_slug}/checkout-key",
    )


def transform(
    raw: list[dict[str, Any]],
    project_slug: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{project_slug}:{item['fingerprint']}",
            "fingerprint": item["fingerprint"],
            "type": item.get("type"),
            "preferred": item.get("preferred"),
            # The checkout-key endpoint (older v2 surface) returns hyphenated keys.
            "public_key": item.get("public-key"),
            "created_at": parse_iso(item.get("created-at")),
            "project_slug": project_slug,
        }
        for item in raw
    ]


@timeit
def load_checkout_keys(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCICheckoutKeySchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCICheckoutKeySchema(), common_job_parameters).run(
        neo4j_session
    )
