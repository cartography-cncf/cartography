import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.keycloak.util import get_paginated
from cartography.models.keycloak.group import KeycloakGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
) -> None:
    groups = get(
        api_session,
        base_url,
        common_job_parameters["REALM"],
    )
    transformed_groups = transform(groups)
    load_groups(
        neo4j_session,
        transformed_groups,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def _get_subgroups(
    api_session: requests.Session,
    base_url: str,
    realm: str,
    group_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    url = f"{base_url}/admin/realms/{realm}/groups/{group_id}/children"
    for group in get_paginated(
        api_session,
        url,
    ):
        group["_members"] = _get_members(api_session, base_url, realm, group["id"])
        result.append(group)
        if group.get("subGroupCount", 0) > 0:
            result.extend(_get_subgroups(api_session, base_url, realm, group["id"]))
    return result


@timeit
def _get_members(
    api_session: requests.Session,
    base_url: str,
    realm: str,
    group_id: str,
) -> list[dict[str, Any]]:
    url = f"{base_url}/admin/realms/{realm}/groups/{group_id}/members"
    return list(get_paginated(api_session, url))


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    realm: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    url = f"{base_url}/admin/realms/{realm}/groups"
    for group in get_paginated(api_session, url, params={"briefRepresentation": False}):
        group["_members"] = _get_members(api_session, base_url, realm, group["id"])
        result.append(group)
        if group.get("subGroupCount", 0) > 0:
            result.extend(_get_subgroups(api_session, base_url, realm, group["id"]))
    return result


def transform(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for group in groups:
        # Transform members to a list of IDs for easier relationship handling
        group["_member_ids"] = [m["id"] for m in group["_members"]]
        group.pop("_members")
        # Transform roles to a list of role names for easier relationship handling
        group["_roles"] = []
        for role_name in group.get("realmRoles", []):
            group["_roles"].append(role_name)
            group.pop("realmRoles", None)
        for roles in group.get("clientRoles", {}).values():
            for role_name in roles:
                group["_roles"].append(role_name)
        group.pop("clientRoles", None)
    return groups


@timeit
def load_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Keycloak Groups (%s) into Neo4j.", len(data), realm)
    load(
        neo4j_session,
        KeycloakGroupSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(KeycloakGroupSchema(), common_job_parameters).run(
        neo4j_session
    )
