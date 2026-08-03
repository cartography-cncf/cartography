"""Snowflake programmatic access tokens.

Tokens have no REST endpoint, so they come from
``SHOW USER PROGRAMMATIC ACCESS TOKENS``. That statement returns every user's tokens
only when the connecting role holds ``MANAGE GRANTS``; without it Snowflake returns
just the tokens of the user Cartography authenticated as. There is no way to tell
the two situations apart from the response, so a thin result is reported as a
coverage warning rather than treated as "this account has one token".
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
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every readable programmatic access token, or None when not permitted."""
    try:
        return client.run_sql("SHOW USER PROGRAMMATIC ACCESS TOKENS")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "programmatic access tokens",
            "SHOW USER PROGRAMMATIC ACCESS TOKENS is not permitted",
        )
        return None


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
                "mins_to_bypass_network_policy_requirement": to_int(
                    token.get("mins_to_bypass_network_policy_requirement"),
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

    Returns whether the listing could be read. When it could not, the caller skips
    token cleanup so previously collected tokens are not deleted.
    """
    tokens = get(client)
    if tokens is None:
        return False

    transformed = transform(tokens, users, client.account_id)
    unowned = [token for token in transformed if not token["user_id"]]
    if unowned:
        logger.warning(
            "%d of %d Snowflake access tokens name a user that is not in the graph; "
            "their ownership edges are omitted.",
            len(unowned),
            len(transformed),
        )
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
    return True
