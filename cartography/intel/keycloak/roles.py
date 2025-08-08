import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.keycloak.util import get_paginated
from cartography.models.keycloak.role import KeycloakRoleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    common_job_parameters: dict[str, Any],
    client_ids: list[str],
) -> None:
    roles = get(api_session, base_url, common_job_parameters["REALM"], client_ids)
    ordered_roles = _order_dicts_dfs(
        roles, children_key="_composite_roles", ignore_unknown_children=True
    )
    load_roles(
        neo4j_session,
        ordered_roles,
        common_job_parameters["REALM"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session, base_url: str, realm: str, client_ids: list[str]
) -> list[dict[str, Any]]:
    roles_by_id: dict[str, dict[str, Any]] = {}

    # Get roles at the REALM level
    url = f"{base_url}/admin/realms/{realm}/roles"
    for role in get_paginated(api_session, url, params={"briefRepresentation": False}):
        if role.get("composite", False):
            # If the role is composite, we need to get its composites
            composite_roles = get_paginated(
                api_session,
                f"{base_url}/admin/realms/{realm}/roles-by-id/{role['id']}/composites",
            )
            role["_composite_roles"] = [
                composite_role["id"] for composite_role in composite_roles
            ]
        roles_by_id[role["id"]] = role

    # Get roles for each client
    for client_id in client_ids:
        url = f"{base_url}/admin/realms/{realm}/clients/{client_id}/roles"
        for role in get_paginated(
            api_session, url, params={"briefRepresentation": False}
        ):
            # If the role is composite, we need to get its composites
            composite_roles = get_paginated(
                api_session,
                f"{base_url}/admin/realms/{realm}/roles-by-id/{role['id']}/composites",
            )
            role["_composite_roles"] = [
                composite_role["id"] for composite_role in composite_roles
            ]
            roles_by_id[role["id"]] = role
    return list(roles_by_id.values())


@timeit
def load_roles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    realm: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Keycloak Roles (%s) into Neo4j.", len(data), realm)
    load(
        neo4j_session,
        KeycloakRoleSchema(),
        data,
        LASTUPDATED=update_tag,
        REALM=realm,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(KeycloakRoleSchema(), common_job_parameters).run(
        neo4j_session
    )


def _order_dicts_dfs(
    nodes: list[dict[str, Any]],
    children_key: str = "children",
    ignore_unknown_children: bool = False,
) -> list[dict[str, Any]]:
    by_id = {n["id"]: n for n in nodes}

    WHITE, GRAY, BLACK = 0, 1, 2  # unvisited, in stack, done
    state: dict[str, int] = {}
    ordered: list[dict[str, Any]] = []

    def visit(node_id: str, path: list[str]) -> None:
        s = state.get(node_id, WHITE)
        if s == GRAY:
            cycle = " -> ".join(path + [node_id])
            raise ValueError(f"Cycle detected: {cycle}")
        if s == BLACK:
            return

        state[node_id] = GRAY
        node = by_id[node_id]

        for child_id in node.get(children_key, []):
            if child_id not in by_id:
                if ignore_unknown_children:
                    continue
                raise KeyError(f"Unknown child id: {child_id}")
            visit(child_id, path + [node_id])

        state[node_id] = BLACK
        ordered.append(node)  # post-order: children before parent

    for nid in by_id:
        if state.get(nid, WHITE) == WHITE:
            visit(nid, [])

    return ordered
