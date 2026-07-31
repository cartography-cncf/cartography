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
from cartography.models.supabase.branch import SupabaseBranchSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    project_ref = common_job_parameters["PROJECT_REF"]
    branches = get(api_session, common_job_parameters["BASE_URL"], project_ref)
    if branches is None:
        warn_unavailable("database branches", project_ref)
        return
    load_branches(
        neo4j_session,
        transform_branches(branches),
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
    """
    List the project's database preview branches.

    Branching is a paid feature tied to the GitHub integration, so on free-tier or
    non-integrated projects this returns a tolerated status and the sync moves on.
    """
    return get_json(
        api_session,
        f"{base_url}/v1/projects/{project_ref}/branches",
        tolerate=TOLERATED_STATUSES,
    )


def transform_branches(
    branches: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [
        {
            "id": branch["id"],
            "name": branch["name"],
            "project_ref": branch["project_ref"],
            "parent_project_ref": branch["parent_project_ref"],
            "is_default": branch.get("is_default"),
            "persistent": branch.get("persistent"),
            "with_data": branch.get("with_data"),
            "status": branch.get("status"),
            "preview_project_status": branch.get("preview_project_status"),
            "git_branch": branch.get("git_branch"),
            "pr_number": branch.get("pr_number"),
            "created_at": iso_to_datetime(branch.get("created_at")),
            "updated_at": iso_to_datetime(branch.get("updated_at")),
            "review_requested_at": iso_to_datetime(branch.get("review_requested_at")),
            "deletion_scheduled_at": iso_to_datetime(
                branch.get("deletion_scheduled_at"),
            ),
        }
        for branch in branches or []
    ]


@timeit
def load_branches(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    project_ref: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SupabaseBranchSchema(),
        data,
        lastupdated=update_tag,
        PROJECT_REF=project_ref,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SupabaseBranchSchema(), common_job_parameters).run(
        neo4j_session,
    )
