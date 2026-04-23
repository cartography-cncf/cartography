import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.graph.job import GraphJob
from cartography.models.keycloak.inheritance import (
    KeycloakRoleIndirectGrantsScopeMatchLink,
)
from cartography.models.keycloak.inheritance import KeycloakUserAssumeScopeMatchLink
from cartography.models.keycloak.inheritance import (
    KeycloakUserInheritedMemberOfGroupMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

_SUB_RESOURCE_LABEL = "KeycloakRealm"

_INHERITED_MEMBER_OF_QUERY = """
    MATCH (:KeycloakRealm {name: $REALM})-[:RESOURCE]->(u:KeycloakUser)
          -[:MEMBER_OF]->(:KeycloakGroup)-[:SUBGROUP_OF*1..5]->(pg:KeycloakGroup)
    RETURN DISTINCT u.id AS user_id, pg.id AS group_id
"""

_ASSUME_ROLE_VIA_GROUP_QUERY = """
    MATCH (:KeycloakRealm {name: $REALM})-[:RESOURCE]->(u:KeycloakUser)
          -[:MEMBER_OF|INHERITED_MEMBER_OF]->(:KeycloakGroup)-[:GRANTS]->(r:KeycloakRole)
    MERGE (u)-[rel:ASSUME_ROLE]->(r)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $UPDATE_TAG
"""

_INDIRECT_GRANTS_QUERY = """
    MATCH (:KeycloakRealm {name: $REALM})-[:RESOURCE]->(r:KeycloakRole)
          -[:INCLUDES*1..5]->(:KeycloakRole)-[:GRANTS]->(s:KeycloakScope)
    RETURN DISTINCT r.id AS role_id, s.id AS scope_id
"""

_ASSUME_SCOPE_QUERY = """
    MATCH (:KeycloakRealm {name: $REALM})-[:RESOURCE]->(u:KeycloakUser)
          -[:ASSUME_ROLE]->(:KeycloakRole)-[:GRANTS|INDIRECT_GRANTS]->(s:KeycloakScope)
    RETURN DISTINCT u.id AS user_id, s.id AS scope_id
"""

_ASSUME_SCOPE_ORPHAN_QUERY = """
    MATCH (realm:KeycloakRealm {name: $REALM})-[:RESOURCE]->(s:KeycloakScope)
    WHERE NOT (s)<-[:GRANTS|INDIRECT_GRANTS]-(:KeycloakRole)
    MATCH (realm)-[:RESOURCE]->(u:KeycloakUser)
    RETURN DISTINCT u.id AS user_id, s.id AS scope_id
"""


@timeit
def sync(
    neo4j_session: neo4j.Session,
    realms: list[dict[str, Any]],
    common_job_parameters: dict[str, Any],
) -> None:
    update_tag = common_job_parameters["UPDATE_TAG"]
    for realm in realms:
        realm_name = realm["realm"]
        _sync_realm_inheritance(neo4j_session, realm_name, update_tag)
        _cleanup_realm(neo4j_session, realm_name, update_tag)


@timeit
def _sync_realm_inheritance(
    neo4j_session: neo4j.Session,
    realm_name: str,
    update_tag: int,
) -> None:
    logger.info("Computing keycloak inheritance for realm '%s'.", realm_name)

    inherited_members = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _INHERITED_MEMBER_OF_QUERY,
        REALM=realm_name,
    )
    if inherited_members:
        load_matchlinks(
            neo4j_session,
            KeycloakUserInheritedMemberOfGroupMatchLink(),
            inherited_members,
            lastupdated=update_tag,
            _sub_resource_label=_SUB_RESOURCE_LABEL,
            _sub_resource_id=realm_name,
        )

    neo4j_session.run(
        _ASSUME_ROLE_VIA_GROUP_QUERY,
        REALM=realm_name,
        UPDATE_TAG=update_tag,
    )

    indirect_grants = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _INDIRECT_GRANTS_QUERY,
        REALM=realm_name,
    )
    if indirect_grants:
        load_matchlinks(
            neo4j_session,
            KeycloakRoleIndirectGrantsScopeMatchLink(),
            indirect_grants,
            lastupdated=update_tag,
            _sub_resource_label=_SUB_RESOURCE_LABEL,
            _sub_resource_id=realm_name,
        )

    scope_assignments = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _ASSUME_SCOPE_QUERY,
        REALM=realm_name,
    )
    orphan_scopes = neo4j_session.execute_read(
        read_list_of_dicts_tx,
        _ASSUME_SCOPE_ORPHAN_QUERY,
        REALM=realm_name,
    )
    all_scope_assignments = _merge_scope_assignments(scope_assignments, orphan_scopes)
    if all_scope_assignments:
        load_matchlinks(
            neo4j_session,
            KeycloakUserAssumeScopeMatchLink(),
            all_scope_assignments,
            lastupdated=update_tag,
            _sub_resource_label=_SUB_RESOURCE_LABEL,
            _sub_resource_id=realm_name,
        )


def _merge_scope_assignments(
    role_based: list[dict[str, str]],
    orphans: list[dict[str, str]],
) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    merged: list[dict[str, str]] = []
    for row in (*role_based, *orphans):
        key = (row["user_id"], row["scope_id"])
        if key not in seen:
            seen.add(key)
            merged.append(row)
    return merged


@timeit
def _cleanup_realm(
    neo4j_session: neo4j.Session,
    realm_name: str,
    update_tag: int,
) -> None:
    for matchlink in (
        KeycloakUserInheritedMemberOfGroupMatchLink(),
        KeycloakRoleIndirectGrantsScopeMatchLink(),
        KeycloakUserAssumeScopeMatchLink(),
    ):
        GraphJob.from_matchlink(
            matchlink,
            _SUB_RESOURCE_LABEL,
            realm_name,
            update_tag,
        ).run(neo4j_session)
