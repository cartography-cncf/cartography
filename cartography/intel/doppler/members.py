from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import paginated_get
from cartography.models.doppler.project_membership import DopplerGroupToProjectMatchLink
from cartography.models.doppler.project_membership import (
    DopplerServiceAccountToProjectMatchLink,
)
from cartography.models.doppler.project_membership import DopplerUserToProjectMatchLink
from cartography.util import timeit

# Maps a Doppler project-member `type` to its MatchLink schema. The `invite` type is
# intentionally absent: there is no node to link a pending invite to.
_MEMBER_LINKS = {
    "workplace_user": DopplerUserToProjectMatchLink(),
    "group": DopplerGroupToProjectMatchLink(),
    "service_account": DopplerServiceAccountToProjectMatchLink(),
}


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    project_slugs: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    members_by_type = get(api_session, common_job_parameters["BASE_URL"], project_slugs)
    load_members(
        neo4j_session,
        members_by_type,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    project_slugs: list[str],
) -> dict[str, list[dict[str, Any]]]:
    members_by_type: dict[str, list[dict[str, Any]]] = {
        member_type: [] for member_type in _MEMBER_LINKS
    }
    for project in project_slugs:
        for member in paginated_get(
            api_session,
            f"{base_url}/projects/project/members",
            "members",
            params={"project": project},
        ):
            member_type = member.get("type")
            if member_type not in members_by_type:
                continue
            role = member.get("role") or {}
            members_by_type[member_type].append(
                {
                    "slug": member["slug"],
                    "project": project,
                    "role": role.get("identifier"),
                    "access_all_environments": member.get("access_all_environments"),
                }
            )
    return members_by_type


@timeit
def load_members(
    neo4j_session: neo4j.Session,
    members_by_type: dict[str, list[dict[str, Any]]],
    workplace_id: str,
    update_tag: int,
) -> None:
    for member_type, link in _MEMBER_LINKS.items():
        load_matchlinks(
            neo4j_session,
            link,
            members_by_type[member_type],
            lastupdated=update_tag,
            _sub_resource_label="DopplerWorkplace",
            _sub_resource_id=workplace_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    for link in _MEMBER_LINKS.values():
        GraphJob.from_matchlink(
            link,
            "DopplerWorkplace",
            common_job_parameters["WORKPLACE_ID"],
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)
