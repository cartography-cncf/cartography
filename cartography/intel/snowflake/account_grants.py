"""Snowflake account-level grants.

``SHOW GRANTS ON ACCOUNT`` is the only source of the privileges granted on the
account object itself, and those are the privileges that matter most: ``MANAGE
GRANTS`` lets a role rewrite the entire grant graph, ``CREATE USER`` and ``CREATE
ROLE`` let it mint identities, ``APPLY MASKING POLICY`` lets it unmask data. None of
them appear on any REST endpoint and none of them appear in a role's own grant
listing, so without this statement the top of the privilege graph is simply missing.

The rows land on the same ``HAS_PRIVILEGE`` edge the rest of the grant graph uses, by
reusing the grant sync's aggregation so that one edge per role carries every
privilege it holds on the account rather than one edge per privilege.
"""

import logging
from collections import defaultdict
from typing import Any

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.grants import transform_grants
from cartography.intel.snowflake.sql_values import to_bool
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.grant import SnowflakeGrantMatchLink
from cartography.util import timeit

logger = logging.getLogger(__name__)

_ACCOUNT_SECURABLE_TYPE = "ACCOUNT"
_ROLE_GRANTEE = "ROLE"


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every privilege granted on the account, or None when not permitted."""
    try:
        return client.run_sql("SHOW GRANTS ON ACCOUNT")
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "account-level grants", "SHOW GRANTS ON ACCOUNT is not permitted"
        )
        return None


def transform(
    grants: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """Aggregate the per-privilege rows into one edge per grantee role.

    Only role grantees are kept: Snowflake grants account-level privileges to roles,
    and a row with any other grantee kind would not resolve to a principal node.

    The rows are reshaped into the same structure the grant sync produces so its
    aggregation is reused rather than reimplemented. That aggregation resolves an
    ``ACCOUNT`` target to the account's own node id, which is why the account locator
    reported in ``name`` is not used to build the key.
    """
    grants_by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for grant in grants:
        grantee_name = to_text(grant.get("grantee_name"))
        privilege = to_text(grant.get("privilege"))
        if not grantee_name or not privilege:
            continue
        if to_text(grant.get("granted_to")) != _ROLE_GRANTEE:
            continue
        grants_by_role[grantee_name].append(
            {
                "securable": {"name": to_text(grant.get("name"))},
                "securable_type": _ACCOUNT_SECURABLE_TYPE,
                "privileges": [privilege],
                "grant_option": to_bool(grant.get("grant_option")),
                "granted_by": to_text(grant.get("granted_by")),
            },
        )

    # SHOW GRANTS ON ACCOUNT only ever names account roles, so there are no
    # database-role grantees to distinguish here.
    edges, unmodelled = transform_grants(dict(grants_by_role), set(), account_id)
    if unmodelled:
        logger.debug(
            "Skipped %d account-level Snowflake grant rows that did not resolve.",
            unmodelled,
        )
    return edges


def load_account_grants(
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


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_matchlink(
        SnowflakeGrantMatchLink(),
        "SnowflakeAccount",
        common_job_parameters["ACCOUNT_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    common_job_parameters: dict,
) -> bool:
    """Sync the privileges granted on the account object.

    Runs after the roles so every grantee resolves on the first pass, and its edges
    share the grant relationship with the per-role grant sync, so both must have run
    before that relationship is cleaned up.

    Returns whether the listing could be read. When it could not, the caller skips
    grant cleanup so previously collected grants are not deleted.
    """
    grants = get(client)
    if grants is None:
        return False

    edges = transform(grants, client.account_id)
    logger.info(
        "Loading %d account-level Snowflake grant edges for account %s.",
        len(edges),
        client.account_id,
    )
    load_account_grants(
        neo4j_session,
        edges,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
