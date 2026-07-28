import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.supabase.util import get_json
from cartography.intel.supabase.util import iso_to_datetime
from cartography.intel.supabase.util import TOLERATED_STATUSES
from cartography.intel.supabase.util import warn_unavailable
from cartography.models.supabase.storagebucket import SupabaseStorageBucketSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    project_ref = common_job_parameters["PROJECT_REF"]
    buckets = get(api_session, common_job_parameters["BASE_URL"], project_ref)
    if buckets is None:
        warn_unavailable("storage buckets", project_ref)
        return
    load_buckets(
        neo4j_session,
        transform_buckets(buckets, project_ref),
        project_ref,
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_ref: str,
) -> list[dict[str, Any]]:
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/storage/buckets",
        tolerate=TOLERATED_STATUSES,
    )


def transform_buckets(
    buckets: list[dict[str, Any]] | None,
    project_ref: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{project_ref}/{bucket['id']}",
            "bucket_id": bucket["id"],
            "name": bucket["name"],
            "public": bucket.get("public"),
            "owner": bucket.get("owner"),
            "created_at": iso_to_datetime(bucket.get("created_at")),
            "updated_at": iso_to_datetime(bucket.get("updated_at")),
        }
        for bucket in buckets or []
    ]


@timeit
def load_buckets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseStorageBucketSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        SupabaseStorageBucketSchema(),
        common_job_parameters,
    ).run(neo4j_session)
