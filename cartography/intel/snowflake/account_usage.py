"""The ``SNOWFLAKE.ACCOUNT_USAGE`` path for roles, grants and role assignments.

The object API and ``SHOW GRANTS`` only report what the collector's own role can
see. ``SHOW ROLES`` in particular follows role visibility, so without
``MANAGE GRANTS`` it returns a *successful but incomplete* list, with nothing in
the response to say so. Treating that as the truth is what lets cleanup delete
roles the collector merely could not see.

``ACCOUNT_USAGE`` has no such blind spot: the views are account-wide and reading
them needs only ``IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE``, which grants no
write capability anywhere. So when these views are readable they are the
authoritative source and the sync can honestly report itself complete; when they
are not, the module falls back to the per-role REST walk and reports incomplete so
cleanup is skipped.

Three views are used, all of them soft-delete rather than remove rows, so every
query filters ``DELETED_ON IS NULL``:

- ``ROLES`` for the role inventory, covering account roles and database roles and
  distinguishing them by ``ROLE_TYPE``.
- ``GRANTS_TO_ROLES`` for every privilege held by a role, and for the role
  hierarchy (a role granted to a role arrives as ``USAGE`` on a ``ROLE``).
- ``GRANTS_TO_USERS`` for role assignments to users.

Rows are reshaped into exactly the shape the REST endpoints return, so
``grants.transform_grants`` and ``grants.transform_role_assignments`` are shared by
both paths rather than duplicated per source.

The cost of this path is staleness: ``ACCOUNT_USAGE`` lags reality by up to two
hours, so a role created minutes ago may be missing. That is a deliberate trade for
not requiring a privilege that can also grant and revoke access account-wide.
"""

import logging
from typing import Any

from cartography.intel.snowflake.sql_values import to_bool
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.util import timeit

logger = logging.getLogger(__name__)

# ROLE_TYPE values. INSTANCE_ROLE and APPLICATION_ROLE belong to Snowflake Native
# Apps and classes, which this module does not model, so they are filtered out
# rather than loaded as account roles.
ACCOUNT_ROLE = "ROLE"
DATABASE_ROLE = "DATABASE_ROLE"

_ROLES_QUERY = """
SELECT name, role_type, role_database_name, owner, owner_role_type, comment,
       created_on
FROM snowflake.account_usage.roles
WHERE deleted_on IS NULL
"""

_GRANTS_TO_ROLES_QUERY = """
SELECT privilege, granted_on, name, table_catalog, table_schema, granted_to,
       grantee_name, grant_option, granted_by, created_on
FROM snowflake.account_usage.grants_to_roles
WHERE deleted_on IS NULL
"""

_GRANTS_TO_USERS_QUERY = """
SELECT role, granted_to, grantee_name, granted_by, created_on
FROM snowflake.account_usage.grants_to_users
WHERE deleted_on IS NULL
"""

# GRANTED_ON values that mean "this row is a role granted to a principal" rather
# than "this principal holds a privilege on an object".
_ROLE_SECURABLE_TYPES = {ACCOUNT_ROLE, DATABASE_ROLE}


def _run(client: SnowflakeClient, statement: str, resource: str) -> list[dict] | None:
    """Run one ACCOUNT_USAGE query, or return None when the view is not readable."""
    try:
        return client.run_sql(statement)
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            resource,
            "SNOWFLAKE.ACCOUNT_USAGE is not readable; the collector role is missing "
            "IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE",
        )
        return None


@timeit
def get_roles(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every live role in the account, or None when ACCOUNT_USAGE is unreadable."""
    return _run(client, _ROLES_QUERY, "roles from ACCOUNT_USAGE")


@timeit
def get_grants_to_roles(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every live grant to a role, or None when ACCOUNT_USAGE is unreadable."""
    return _run(client, _GRANTS_TO_ROLES_QUERY, "grants from ACCOUNT_USAGE")


@timeit
def get_grants_to_users(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every live role assignment to a user, or None when unreadable."""
    return _run(client, _GRANTS_TO_USERS_QUERY, "role assignments from ACCOUNT_USAGE")


def split_roles(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split ACCOUNT_USAGE role rows into ``(account roles, database roles)``.

    Both are returned shaped like the REST payloads their own syncs already accept,
    so neither transform has to learn about this source. The per-role counters the
    object API reports (``assigned_to_users`` and friends) have no ACCOUNT_USAGE
    equivalent and are left absent rather than guessed at; the edges those counts
    summarise are built from the grant views instead, which is strictly better.
    """
    account_roles: list[dict[str, Any]] = []
    database_roles: list[dict[str, Any]] = []

    for row in rows:
        role_type = to_text(row.get("role_type"))
        name = to_text(row.get("name"))
        if not name:
            continue
        common = {
            "name": name,
            "comment": to_text(row.get("comment")),
            "owner": to_text(row.get("owner")) or None,
            "owner_role_type": to_text(row.get("owner_role_type")),
            "created_on": row.get("created_on"),
        }
        if role_type == ACCOUNT_ROLE:
            account_roles.append(common)
        elif role_type == DATABASE_ROLE:
            database_name = to_text(row.get("role_database_name"))
            if not database_name:
                logger.warning(
                    "Skipping Snowflake database role %s: ACCOUNT_USAGE reported no "
                    "database for it.",
                    name,
                )
                continue
            database_roles.append({**common, "database_name": database_name})

    return account_roles, database_roles


def split_grants(
    grants_to_roles: list[dict[str, Any]],
    grants_to_users: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    """Reshape the two grant views into the REST-shaped structures grants.py expects.

    Returns ``(grants_by_role, grants_of_by_role)``:

    - ``grants_by_role`` maps a grantee to the privileges it holds, one row per
      privilege, matching ``SHOW GRANTS TO ROLE``. ``grants.transform_grants`` then
      aggregates them into one edge per (principal, object) pair.
    - ``grants_of_by_role`` maps a *granted* role to the principals holding it,
      matching ``SHOW GRANTS OF ROLE``, and feeds the role-hierarchy and role
      assignment edges.

    A role granted to another role appears in ``GRANTS_TO_ROLES`` as ``USAGE`` on a
    ``ROLE``, so such a row contributes to both structures: it is a privilege the
    grantee holds *and* an edge in the role hierarchy. That is exactly what the REST
    path produces, where the same fact shows up under both ``grants`` and
    ``grants-of``, so keeping both here means the two paths build the same graph.
    """
    grants_by_role: dict[str, list[dict[str, Any]]] = {}
    grants_of_by_role: dict[str, list[dict[str, Any]]] = {}

    for row in grants_to_roles:
        raw_grantee = to_text(row.get("grantee_name"))
        privilege = to_text(row.get("privilege"))
        granted_on = to_text(row.get("granted_on"))
        name = to_text(row.get("name"))
        if not raw_grantee or not privilege or not granted_on or not name:
            continue
        # The grantee keys both structures and is turned into a node id downstream,
        # so it has to be spelled the way the role node's own id was built. GRANTED_TO
        # says which kind it is, which is more reliable than looking for a dot: an
        # account role name may legally contain one.
        grantee = normalize_role_reference(
            raw_grantee,
            is_database_role=to_text(row.get("granted_to")) == DATABASE_ROLE,
        )

        grants_by_role.setdefault(grantee, []).append(
            {
                "securable": {
                    "name": name,
                    "database": to_text(row.get("table_catalog")),
                    "schema": to_text(row.get("table_schema")),
                },
                "securable_type": granted_on,
                "privileges": [privilege],
                "grant_option": to_bool(row.get("grant_option")),
                "granted_by": to_text(row.get("granted_by")) or None,
            },
        )

        # `GRANT ROLE a TO ROLE b` is recorded as USAGE on ROLE a held by b, which is
        # the only place the role hierarchy appears in this view.
        if granted_on in _ROLE_SECURABLE_TYPES and privilege == "USAGE":
            granted_role = _granted_role_name(row, granted_on, name)
            grants_of_by_role.setdefault(granted_role, []).append(
                {
                    "role": granted_role,
                    "grantee_name": grantee,
                    "granted_to": to_text(row.get("granted_to")),
                    "granted_by": to_text(row.get("granted_by")) or None,
                    "created_on": row.get("created_on"),
                },
            )

    for row in grants_to_users:
        # GRANTS_TO_USERS only ever grants account roles, whose ids are built from the
        # bare name, so neither value needs requalifying.
        role = to_text(row.get("role"))
        user_name = to_text(row.get("grantee_name"))
        if not role or not user_name:
            continue
        grants_of_by_role.setdefault(role, []).append(
            {
                "role": role,
                "grantee_name": user_name,
                # This view holds nothing but user assignments, and older rows leave
                # granted_to empty, so it is asserted rather than read.
                "granted_to": "USER",
                "granted_by": to_text(row.get("granted_by")) or None,
                "created_on": row.get("created_on"),
            },
        )

    return grants_by_role, grants_of_by_role


def _granted_role_name(row: dict[str, Any], granted_on: str, name: str) -> str:
    """Qualify the name of the role being granted, for a USAGE-on-ROLE row.

    A database role has to carry its database to match the id its node was loaded
    under. ``TABLE_CATALOG`` holds that database for a ``DATABASE_ROLE`` row.
    """
    if granted_on != DATABASE_ROLE:
        return name
    database = to_text(row.get("table_catalog"))
    if not database:
        # Already database-qualified in NAME, so only the quoting has to be rebuilt.
        return normalize_role_reference(name, is_database_role=True)
    return sf_fqn(database, name)


def normalize_role_reference(reference: str, is_database_role: bool) -> str:
    """Spell a role reference the way the role node's own id was built.

    The two role kinds are keyed differently, so this cannot be uniform:

    - An account role's id is built from its bare name exactly as reported, so the
      reference is returned untouched.
    - A database role's id is built from ``sf_fqn(database, name)``, which quotes any
      component that is not a plain uppercase identifier. ``ACCOUNT_USAGE`` reports
      the pair unquoted as ``mydb.myrole``, so without rebuilding it through
      ``sf_fqn`` a database role created with a quoted, non-uppercase name silently
      loses every hierarchy and privilege edge: the MatchLink matches nothing.

    The components are the *stored* names rather than SQL source text, so they are
    split on the dot and passed to ``sf_fqn`` verbatim. They are deliberately not run
    through ``split_qualified_name``, which folds an unquoted component to uppercase
    and would corrupt a legitimately lowercase stored name.

    A stored name containing a literal dot cannot be told apart from the
    database/role separator in this view, so it is left as reported rather than
    guessed at.
    """
    if not is_database_role:
        return reference
    parts = reference.split(".")
    if len(parts) != 2 or not all(parts):
        return reference
    return sf_fqn(*parts)
