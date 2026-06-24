import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import _TIMEOUT
from cartography.intel.doppler.util import paginated_get
from cartography.models.doppler.group import DopplerGroupMembershipMatchLink
from cartography.models.doppler.group import DopplerGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    groups, memberships, memberships_complete = get(
        api_session, common_job_parameters["BASE_URL"]
    )
    groups = transform(groups)
    load_groups(
        neo4j_session,
        groups,
        memberships,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters, memberships_complete)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    """Returns (groups, memberships, memberships_complete). memberships_complete is
    False only when there were groups to query but every member fetch failed."""
    groups = paginated_get(api_session, f"{base_url}/workplace/groups", "groups")
    memberships: list[dict[str, Any]] = []
    success = False
    for group in groups:
        slug = group["slug"]
        # Best-effort: a single group's member fetch failing (e.g. it was deleted
        # mid-sync, or a permissions edge case) should not abort the whole workplace
        # sync, so log and skip that group's memberships.
        try:
            req = api_session.get(
                f"{base_url}/workplace/groups/group/{slug}", timeout=_TIMEOUT
            )
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.warning(
                "Failed to fetch members for Doppler group %s, skipping: %s", slug, e
            )
            continue
        success = True
        members = req.json().get("group", {}).get("members", []) or []
        for member in members:
            memberships.append({"user_id": member["slug"], "group_slug": slug})
    return groups, memberships, (success or not groups)


def transform(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for group in groups:
        role = group.get("default_project_role") or {}
        group["default_project_role"] = role.get("identifier")
    return groups


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    groups: list[dict[str, Any]],
    memberships: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerGroupSchema(),
        groups,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )
    load_matchlinks(
        neo4j_session,
        DopplerGroupMembershipMatchLink(),
        memberships,
        lastupdated=update_tag,
        _sub_resource_label="DopplerWorkplace",
        _sub_resource_id=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    memberships_complete: bool = True,
) -> None:
    # Group nodes come from the authoritative list endpoint, so always prune them.
    GraphJob.from_node_schema(DopplerGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
    # Only prune membership edges if at least one group's members were fetched; an
    # all-fail run would otherwise delete every MEMBER_OF edge.
    if memberships_complete:
        GraphJob.from_matchlink(
            DopplerGroupMembershipMatchLink(),
            "DopplerWorkplace",
            common_job_parameters["WORKPLACE_ID"],
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)
    else:
        logger.warning(
            "Skipping DopplerGroup membership cleanup: no group member fetch "
            "succeeded this run, preserving existing edges."
        )
