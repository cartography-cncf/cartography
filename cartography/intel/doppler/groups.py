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


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    groups, memberships = get(api_session, common_job_parameters["BASE_URL"])
    groups = transform(groups)
    load_groups(
        neo4j_session,
        groups,
        memberships,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups = paginated_get(api_session, f"{base_url}/workplace/groups", "groups")
    memberships: list[dict[str, Any]] = []
    for group in groups:
        slug = group["slug"]
        req = api_session.get(
            f"{base_url}/workplace/groups/group/{slug}", timeout=_TIMEOUT
        )
        req.raise_for_status()
        members = req.json().get("group", {}).get("members", []) or []
        for member in members:
            memberships.append({"user_id": member["slug"], "group_slug": slug})
    return groups, memberships


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
) -> None:
    GraphJob.from_node_schema(DopplerGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_matchlink(
        DopplerGroupMembershipMatchLink(),
        "DopplerWorkplace",
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
