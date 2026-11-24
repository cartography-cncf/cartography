import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.neon.util import get_paginated
from cartography.intel.neon.util import iso_to_datetime
from cartography.models.neon.branch import NeonBranchSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_BRANCHES_PAGE_SIZE = 1000


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync the branches of the project in scope and return them, so the caller can
    fan out to the per-branch resources (roles, databases, buckets, credentials).
    """
    project_id = common_job_parameters["PROJECT_ID"]
    branches = get(api_session, common_job_parameters["BASE_URL"], project_id)
    load_branches(
        neo4j_session,
        transform_branches(branches),
        project_id,
        common_job_parameters["UPDATE_TAG"],
    )
    GraphJob.from_node_schema(NeonBranchSchema(), common_job_parameters).run(
        neo4j_session,
    )
    return branches


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_id: str,
) -> list[dict[str, Any]]:
    # Not tolerated: every Neon project has at least one branch, and a key that
    # can see the project can list them. A failure here is a real error.
    branches = get_paginated(
        api_session,
        f"{base_url}/projects/{project_id}/branches",
        "branches",
        _BRANCHES_PAGE_SIZE,
    )
    return branches or []


def transform_branches(branches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # The API lists children before their parents (newest first). Neo4j still
    # resolves BRANCHED_FROM to a parent merged later in the same batch, which
    # test_neon_full_sync guards, so no reordering is needed.
    return [
        {
            "id": branch["id"],
            "name": branch["name"],
            "parent_id": branch.get("parent_id"),
            "parent_timestamp": iso_to_datetime(branch.get("parent_timestamp")),
            "default": branch.get("default"),
            "primary": branch.get("primary"),
            "protected": branch.get("protected"),
            "current_state": branch.get("current_state"),
            "init_source": branch.get("init_source"),
            "creation_source": branch.get("creation_source"),
            "logical_size": branch.get("logical_size"),
            "created_at": iso_to_datetime(branch.get("created_at")),
            "updated_at": iso_to_datetime(branch.get("updated_at")),
            "expires_at": iso_to_datetime(branch.get("expires_at")),
        }
        for branch in branches
    ]


@timeit
def load_branches(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        NeonBranchSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_ID=project_id,
    )
