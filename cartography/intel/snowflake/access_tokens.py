"""Snowflake programmatic access tokens.

Tokens have no REST endpoint, so they come from
``SHOW USER PROGRAMMATIC ACCESS TOKENS``. Listing another user's tokens requires
``MODIFY PROGRAMMATIC AUTHENTICATION METHODS`` on that user; no account-level
privilege covers it, and ``MANAGE GRANTS`` in particular does not. A USER object has
no plain ``MODIFY`` privilege at all. Without that grant the bare form of the
statement silently returns just the tokens of the user Cartography authenticated as,
and the response gives no way to tell that from a complete answer.

Trusting the bare form would therefore let a permission-limited run look complete and
delete every other user's tokens at cleanup. So the listing is done per user with the
``FOR USER`` form instead: a user whose tokens cannot be read is an explicit error
that marks the surface incomplete, which suppresses cleanup, rather than an invisible
gap in the results.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.sql_values import to_int
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.access_token import (
    SnowflakeProgrammaticAccessTokenSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_for_user(
    client: SnowflakeClient, user_name: str
) -> list[dict[str, Any]] | None:
    """One user's programmatic access tokens, or None when they cannot be read.

    Reading another user's tokens needs ``MODIFY PROGRAMMATIC AUTHENTICATION
    METHODS`` on that user, so a 403-equivalent here is expected on a least-privilege
    collector and must be reported rather than read as "this user has no tokens".
    """
    try:
        return client.run_sql(
            f"SHOW USER PROGRAMMATIC ACCESS TOKENS FOR USER {sf_fqn(user_name)}",
        )
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        return None


@timeit
def get(
    client: SnowflakeClient, users: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Every readable token across every user, plus whether all users were readable."""
    tokens: list[dict[str, Any]] = []
    unreadable: list[str] = []
    for user in users:
        user_tokens = get_for_user(client, user["name"])
        if user_tokens is None:
            unreadable.append(user["name"])
            continue
        tokens.extend(user_tokens)
    if unreadable:
        warn_unavailable(
            "programmatic access tokens",
            f"{len(unreadable)} of {len(users)} users could not be read "
            "(MODIFY PROGRAMMATIC AUTHENTICATION METHODS on each user is required "
            "to see that user's tokens)",
        )
    return tokens, not unreadable


def transform(
    tokens: list[dict[str, Any]],
    users: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """Shape token rows into nodes, resolving each token's owning user.

    The owning user's node id is taken from the already-synced user listing rather
    than recomputed, so a token can only point at a user that is actually in the
    graph. A token whose user was not synced keeps a null owner, which suppresses
    the ownership edge instead of dangling it.
    """
    user_ids_by_name = {user["name"]: user["id"] for user in users}
    transformed: list[dict[str, Any]] = []

    for token in tokens:
        name = token["name"]
        user_name = token["user_name"]
        role_restriction = to_text(token.get("role_restriction"))
        transformed.append(
            {
                "id": sf_id(account_id, "access_token", sf_fqn(user_name, name)),
                "name": name,
                "user_name": user_name,
                "user_id": user_ids_by_name.get(user_name),
                "role_restriction": role_restriction,
                # Role node ids are keyed on the bare role name, matching the role
                # sync; null when the token is unrestricted.
                "role_restriction_id": (
                    sf_id(account_id, "role", role_restriction)
                    if role_restriction
                    else None
                ),
                "status": to_text(token.get("status")),
                # `SHOW ... PROGRAMMATIC ACCESS TOKENS` names this column
                # mins_to_bypass_required_network_policy, while the ALTER parameter
                # that sets it is MINS_TO_BYPASS_NETWORK_POLICY_REQUIREMENT. The two
                # spellings are not interchangeable: reading the parameter name here
                # yields null for every token.
                "mins_to_bypass_required_network_policy": to_int(
                    token.get("mins_to_bypass_required_network_policy"),
                ),
                "rotated_to": to_text(token.get("rotated_to")),
                "comment": to_text(token.get("comment")),
                "created_by": to_text(token.get("created_by")),
                "expires_at": iso_to_datetime(token.get("expires_at")),
                "created_on": iso_to_datetime(token.get("created_on")),
            },
        )

    return transformed


def load_access_tokens(
    neo4j_session: neo4j.Session,
    tokens: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeProgrammaticAccessTokenSchema(),
        tokens,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeProgrammaticAccessTokenSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    users: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync programmatic access tokens.

    Runs after users so every token's ownership edge resolves on the first pass.

    Returns whether every user's tokens could be read. When any could not, the caller
    skips token cleanup so previously collected tokens are not deleted.
    """
    tokens, complete = get(client, users)
    # Every token is fetched per synced user, so its user_name is in the map by
    # construction and the ownership edge always resolves.
    transformed = transform(tokens, users, client.account_id)
    logger.info(
        "Loading %d Snowflake programmatic access tokens for account %s.",
        len(transformed),
        client.account_id,
    )
    load_access_tokens(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return complete
