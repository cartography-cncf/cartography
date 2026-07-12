import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.circleci.util import flatten_labels
from cartography.intel.circleci.util import paginated_get
from cartography.intel.circleci.util import parse_iso
from cartography.models.circleci.component import CircleCIComponentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_PAGE_SIZE = 100


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
    org_id: str,
) -> None:
    raw = get(api_session, common_job_parameters["BASE_URL"], org_id)
    components = transform(raw)
    load_components(
        neo4j_session,
        components,
        org_id,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org_id: str,
) -> list[dict[str, Any]]:
    return paginated_get(
        api_session,
        f"{base_url}/deploy/components",
        params={"org-id": org_id, "page-size": _PAGE_SIZE},
    )


def transform(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": item["id"],
            "name": item.get("name"),
            "project_id": item.get("project_id"),
            "labels": flatten_labels(item.get("labels")),
            "release_count": item.get("release_count"),
            "created_at": parse_iso(item.get("created_at")),
            "updated_at": parse_iso(item.get("updated_at")),
        }
        for item in raw
    ]


@timeit
def load_components(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CircleCIComponentSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(CircleCIComponentSchema(), common_job_parameters).run(
        neo4j_session,
    )
