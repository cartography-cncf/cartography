"""Snowflake grant, role-assignment and role-hierarchy edges.

Snowflake exposes grants per role, so this walks every role: ``grants`` gives the
privileges the role holds, and ``grants-of`` gives every grantee the role has been
granted to, which is simultaneously the user-to-role assignment and the
role-to-role hierarchy.

User-to-role assignments come from ``grants-of`` rather than from
``/users/{name}/grants`` deliberately: both express the same fact, but there are
usually far fewer roles than users, so walking roles costs fewer requests.
"""

import logging
from collections import defaultdict
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.grant import SnowflakeGrantMatchLink
from cartography.models.snowflake.role_grant import (
    SnowflakeDatabaseRoleToDatabaseRoleMatchLink,
)
from cartography.models.snowflake.role_grant import SnowflakeRoleToDatabaseRoleMatchLink
from cartography.models.snowflake.role_grant import SnowflakeRoleToRoleMatchLink
from cartography.models.snowflake.role_grant import SnowflakeServiceUserToRoleMatchLink
from cartography.models.snowflake.role_grant import SnowflakeUserToRoleMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Snowflake's securable_type values, mapped to the object-type segment this module
# uses in node ids. Types absent here are objects Cartography does not model; a
# grant on one of them is counted and logged rather than silently dropped.
#
# On a stock Enterprise account the only unmapped types observed are APPLICATION
# ROLE (Native App application roles), CLASS (Snowpark ML classes) and
# ORGANIZATION PROFILE, none of which this module inventories. A large skip count
# for any other type means a resource type is missing from the module.
SECURABLE_TYPE_TO_OBJECT_TYPE = {
    "ACCOUNT": "account",
    "AGGREGATION POLICY": "data_policy",
    "ALERT": "alert",
    "API INTEGRATION": "api_integration",
    "ARTIFACT REPOSITORY": "artifact_repository",
    "AUTHENTICATION POLICY": "authentication_policy",
    "CATALOG INTEGRATION": "catalog_integration",
    "COMPUTE POOL": "compute_pool",
    "CORTEX SEARCH SERVICE": "cortex_search_service",
    "DATABASE": "database",
    "DATABASE ROLE": "database_role",
    "DYNAMIC TABLE": "dynamic_table",
    "EVENT TABLE": "event_table",
    "EXTERNAL ACCESS INTEGRATION": "external_access_integration",
    "EXTERNAL TABLE": "external_table",
    "EXTERNAL VOLUME": "external_volume",
    "FAILOVER GROUP": "failover_group",
    "FILE FORMAT": "file_format",
    "FUNCTION": "function",
    "ICEBERG TABLE": "iceberg_table",
    "IMAGE REPOSITORY": "image_repository",
    "JOIN POLICY": "data_policy",
    # Snowflake names each integration kind explicitly ("API INTEGRATION",
    # "SECURITY INTEGRATION", ...), and this module models them as separate labels,
    # so there is deliberately no generic "INTEGRATION" entry: mapping it would
    # claim the grant was handled while resolving to no node at all.
    "MASKING POLICY": "data_policy",
    "MATERIALIZED VIEW": "materialized_view",
    "NETWORK POLICY": "network_policy",
    "NETWORK RULE": "network_rule",
    "NOTEBOOK": "notebook",
    "NOTIFICATION INTEGRATION": "notification_integration",
    "PASSWORD POLICY": "password_policy",
    "PIPE": "pipe",
    "PROCEDURE": "procedure",
    "PROJECTION POLICY": "data_policy",
    "REPLICATION GROUP": "replication_group",
    "RESOURCE MONITOR": "resource_monitor",
    "ROLE": "role",
    "ROW ACCESS POLICY": "data_policy",
    "SCHEMA": "schema",
    "SECRET": "secret",
    "SECURITY INTEGRATION": "security_integration",
    "SEQUENCE": "sequence",
    "SERVICE": "service",
    "SESSION POLICY": "session_policy",
    "SHARE": "share",
    "STAGE": "stage",
    "STORAGE INTEGRATION": "storage_integration",
    "STREAM": "stream",
    "STREAMLIT": "streamlit",
    "TABLE": "table",
    "TAG": "tag",
    "TASK": "task",
    "USER": "user",
    "VIEW": "view",
    "WAREHOUSE": "warehouse",
}


def _securable_fqn(securable: dict[str, Any]) -> str | None:
    """Assemble the qualified name of a grant's target object.

    Snowflake returns the target split across ``database``, ``schema`` and
    ``name``, so the qualified name is rebuilt through ``sf_fqn`` to guarantee it
    is quoted exactly the way the object's own node id was built.
    """
    name = securable.get("name")
    if not name:
        return None
    parts = [
        part
        for part in (securable.get("database"), securable.get("schema"), name)
        if part
    ]
    return sf_fqn(*parts)


def securable_id(
    securable: dict[str, Any],
    securable_type: str | None,
    account_id: str,
) -> str | None:
    """Resolve a grant target to the node id of the object it refers to.

    Returns None when Cartography does not model the object type, in which case
    the grant is skipped. Unresolvable ids are harmless in themselves (the
    MatchLink simply matches nothing), but returning None lets the caller report
    coverage instead of silently producing an edge-free load.
    """
    if not securable_type:
        return None
    object_type = SECURABLE_TYPE_TO_OBJECT_TYPE.get(securable_type.upper())
    if not object_type:
        return None
    if object_type == "account":
        # Account-level grants name the account by its *locator*, not by the
        # organization-qualified identifier the account node is keyed on, so the
        # name in the payload cannot be used to build the id.
        return account_id
    fqn = _securable_fqn(securable)
    return sf_id(account_id, object_type, fqn) if fqn else None


@timeit
def get_role_grants(client: SnowflakeClient, role: str) -> list[dict[str, Any]] | None:
    """Privileges held by one role, or None when the role is not readable."""
    try:
        return client.list_all(f"/api/v2/roles/{role}/grants")
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


@timeit
def get_role_grants_of(
    client: SnowflakeClient, role: str
) -> list[dict[str, Any]] | None:
    """Grantees a role has been granted to, or None when not readable."""
    try:
        return client.list_all(f"/api/v2/roles/{role}/grants-of")
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


@timeit
def get_database_role_grants(
    client: SnowflakeClient, database_name: str, role_name: str
) -> list[dict[str, Any]] | None:
    """Privileges held by one database role, or None when it is not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{database_name}/database-roles/{role_name}/grants",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


@timeit
def get_database_role_grants_of(
    client: SnowflakeClient, database_name: str, role_name: str
) -> list[dict[str, Any]] | None:
    """Grantees a database role has been granted to, or None when not readable."""
    try:
        return client.list_all(
            f"/api/v2/databases/{database_name}/database-roles/{role_name}/grants-of",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        return None


def transform_grants(
    grants_by_role: dict[str, list[dict[str, Any]]],
    database_role_names: set[str],
    account_id: str,
) -> tuple[list[dict[str, Any]], int]:
    """Aggregate per-privilege grant rows into one edge per (role, object).

    Snowflake returns a separate row for every privilege, so ``SYSADMIN`` holding
    three privileges on the account arrives as three rows. Collapsing them into a
    single edge with a ``privileges`` list keeps the graph one-edge-per-pair, which
    is what makes the grant graph traversable.

    Returns the edges plus the number of rows skipped because their object type is
    not modelled.
    """
    # (principal id, securable id) -> aggregated edge
    aggregated: dict[tuple[str, str], dict[str, Any]] = {}
    unmodelled = 0

    for role_name, grants in grants_by_role.items():
        # A database role is keyed by its database-qualified name and is a different
        # node label, so it cannot be resolved as an account role.
        principal_id = sf_id(
            account_id,
            "database_role" if role_name in database_role_names else "role",
            role_name,
        )
        for grant in grants:
            target_id = securable_id(
                grant.get("securable") or {},
                grant.get("securable_type"),
                account_id,
            )
            if not target_id:
                unmodelled += 1
                continue
            key = (principal_id, target_id)
            edge = aggregated.get(key)
            if edge is None:
                edge = {
                    "principal_id": principal_id,
                    "securable_id": target_id,
                    "privileges": [],
                    "grant_option": False,
                    "granted_by": grant.get("granted_by") or None,
                }
                aggregated[key] = edge
            edge["privileges"].extend(grant.get("privileges") or [])
            # WITH GRANT OPTION on any privilege makes the grant onward-grantable,
            # which is what matters for an escalation path.
            if grant.get("grant_option"):
                edge["grant_option"] = True

    for edge in aggregated.values():
        edge["privileges"] = sorted(set(edge["privileges"]))
    return list(aggregated.values()), unmodelled


def transform_role_assignments(
    grants_of_by_role: dict[str, list[dict[str, Any]]],
    service_user_names: set[str],
    database_role_names: set[str],
    account_id: str,
) -> dict[str, list[dict[str, Any]]]:
    """Split ``grants-of`` rows into the five role-edge kinds.

    ``granted_to`` distinguishes a user assignment from a role-to-role grant, and
    the grantee's own kind then decides which edge applies. Keyed by edge kind so
    the caller can load each MatchLink separately.
    """
    edges: dict[str, list[dict[str, Any]]] = {
        "user_to_role": [],
        "service_user_to_role": [],
        "role_to_role": [],
        "role_to_database_role": [],
        "database_role_to_database_role": [],
    }

    for role_name, grants_of in grants_of_by_role.items():
        for grant in grants_of:
            grantee_name = grant.get("grantee_name")
            granted_to = (grant.get("granted_to") or "").upper()
            if not grantee_name:
                continue
            # `role` names the granted role; on a database role listing it is
            # already database-qualified.
            granted_role = grant.get("role") or role_name
            is_database_role = granted_role in database_role_names
            common = {
                "role_id": sf_id(
                    account_id,
                    "database_role" if is_database_role else "role",
                    granted_role,
                ),
                "granted_by": grant.get("granted_by") or None,
                "created_on": iso_to_datetime(grant.get("created_on")),
            }

            if granted_to == "USER":
                kind = (
                    "service_user_to_role"
                    if grantee_name in service_user_names
                    else "user_to_role"
                )
                edges[kind].append(
                    {**common, "grantee_id": sf_id(account_id, "user", grantee_name)},
                )
            elif granted_to == "ROLE":
                kind = "role_to_database_role" if is_database_role else "role_to_role"
                edges[kind].append(
                    {**common, "grantee_id": sf_id(account_id, "role", grantee_name)},
                )
            elif granted_to == "DATABASE_ROLE":
                edges["database_role_to_database_role"].append(
                    {
                        **common,
                        "grantee_id": sf_id(account_id, "database_role", grantee_name),
                    },
                )

    return edges


_ROLE_EDGE_MATCHLINKS = {
    "user_to_role": SnowflakeUserToRoleMatchLink(),
    "service_user_to_role": SnowflakeServiceUserToRoleMatchLink(),
    "role_to_role": SnowflakeRoleToRoleMatchLink(),
    "role_to_database_role": SnowflakeRoleToDatabaseRoleMatchLink(),
    "database_role_to_database_role": SnowflakeDatabaseRoleToDatabaseRoleMatchLink(),
}


def load_grants(
    neo4j_session: neo4j.Session,
    grants: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        SnowflakeGrantMatchLink(),
        grants,
        lastupdated=update_tag,
        _sub_resource_label="SnowflakeAccount",
        _sub_resource_id=account_id,
    )


def load_role_assignments(
    neo4j_session: neo4j.Session,
    edges: dict[str, list[dict[str, Any]]],
    account_id: str,
    update_tag: int,
) -> None:
    for kind, matchlink in _ROLE_EDGE_MATCHLINKS.items():
        load_matchlinks(
            neo4j_session,
            matchlink,
            edges[kind],
            lastupdated=update_tag,
            _sub_resource_label="SnowflakeAccount",
            _sub_resource_id=account_id,
        )


def cleanup(
    neo4j_session: neo4j.Session,
    account_id: str,
    update_tag: int,
) -> None:
    GraphJob.from_matchlink(
        SnowflakeGrantMatchLink(), "SnowflakeAccount", account_id, update_tag
    ).run(neo4j_session)
    for matchlink in _ROLE_EDGE_MATCHLINKS.values():
        GraphJob.from_matchlink(
            matchlink, "SnowflakeAccount", account_id, update_tag
        ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    roles: list[dict[str, Any]],
    service_user_names: set[str],
    database_roles: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Materialise every grant, role assignment and role-hierarchy edge.

    Runs last, after every principal and grantable object is in the graph, so the
    edges resolve on the first pass.

    Returns whether the walk was complete. When any role could not be read, the
    caller skips grant cleanup rather than deleting edges it merely failed to
    re-read this run.
    """
    account_id = client.account_id
    database_role_names = {role["qualified_name"] for role in database_roles}

    grants_by_role: dict[str, list[dict[str, Any]]] = {}
    grants_of_by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    complete = True

    for role in roles:
        name = role["name"]
        grants = get_role_grants(client, name)
        if grants is None:
            complete = False
        else:
            grants_by_role[name] = grants

        grants_of = get_role_grants_of(client, name)
        if grants_of is None:
            complete = False
        else:
            grants_of_by_role[name].extend(grants_of)

    # Database roles carry their own privileges and their own hierarchy, and they are
    # enumerated per database rather than under /roles, so they need their own walk.
    # Without it a database role appears in the graph holding nothing.
    for database_role in database_roles:
        qualified_name = database_role["qualified_name"]
        database_name = database_role["database_name"]
        role_name = database_role["name"]

        database_grants = get_database_role_grants(client, database_name, role_name)
        if database_grants is None:
            complete = False
        else:
            grants_by_role[qualified_name] = database_grants

        database_grants_of = get_database_role_grants_of(
            client, database_name, role_name
        )
        if database_grants_of is None:
            complete = False
        else:
            grants_of_by_role[qualified_name].extend(database_grants_of)

    grants, unmodelled = transform_grants(
        grants_by_role, database_role_names, account_id
    )
    if unmodelled:
        logger.info(
            "Skipped %d Snowflake grants on object types Cartography does not model.",
            unmodelled,
        )
    load_grants(neo4j_session, grants, account_id, common_job_parameters["UPDATE_TAG"])

    role_edges = transform_role_assignments(
        grants_of_by_role, service_user_names, database_role_names, account_id
    )
    logger.info(
        "Loading %d Snowflake grant edges and %d role edges for account %s.",
        len(grants),
        sum(len(edges) for edges in role_edges.values()),
        account_id,
    )
    load_role_assignments(
        neo4j_session, role_edges, account_id, common_job_parameters["UPDATE_TAG"]
    )

    if not complete:
        logger.warning(
            "Some Snowflake roles could not be read; skipping grant cleanup so "
            "still-valid edges are not deleted.",
        )
    return complete
