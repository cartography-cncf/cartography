"""Snowflake data governance policies.

Masking, row access, projection, aggregation and join policies are five separate
``SHOW`` commands that return the same columns and describe the same idea: a rule
that restricts what a query may read. They are collected together and loaded onto a
single label with a ``policy_kind`` discriminator, which is also the discriminator
``ACCOUNT_USAGE.POLICY_REFERENCES`` uses for their attachments.

All five are Enterprise-edition features. On a Standard-edition account the very
first statement errors, and the whole surface is skipped so that cleanup does not
delete policies collected while the account was on a higher edition.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.data_policy import SnowflakeDataPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# policy_kind -> the statement that lists that kind. The keys match
# ACCOUNT_USAGE.POLICY_REFERENCES.POLICY_KIND so attachments resolve to these nodes.
POLICY_STATEMENTS = {
    "MASKING_POLICY": "SHOW MASKING POLICIES IN ACCOUNT",
    "ROW_ACCESS_POLICY": "SHOW ROW ACCESS POLICIES IN ACCOUNT",
    "PROJECTION_POLICY": "SHOW PROJECTION POLICIES IN ACCOUNT",
    "AGGREGATION_POLICY": "SHOW AGGREGATION POLICIES IN ACCOUNT",
    "JOIN_POLICY": "SHOW JOIN POLICIES IN ACCOUNT",
}


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every data governance policy of every kind, or None when unreadable.

    Each returned row is the listing row plus the ``policy_kind`` it came from.
    """
    policies: list[dict[str, Any]] = []
    for policy_kind, statement in POLICY_STATEMENTS.items():
        try:
            rows = client.run_sql(statement)
        except SnowflakeSqlError as error:
            if not is_sql_unavailable(error):
                raise
            warn_unavailable(
                "data governance policies",
                f"{statement} is not available on this account edition",
            )
            return None
        policies.extend({**row, "policy_kind": policy_kind} for row in rows)
    return policies


def transform(
    policies: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """Shape listing rows from all five policy kinds into nodes."""
    transformed: list[dict[str, Any]] = []

    for policy in policies:
        database_name = policy["database_name"]
        schema_name = policy["schema_name"]
        name = policy["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        transformed.append(
            {
                # All five kinds share the "data_policy" key segment, which is also
                # what the grant sync resolves a policy grant to.
                "id": sf_id(account_id, "data_policy", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "policy_kind": policy["policy_kind"],
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "kind": to_text(policy.get("kind")),
                "signature": to_text(policy.get("signature")),
                "return_type": to_text(policy.get("return_type")),
                "body": to_text(policy.get("body")),
                "owner": to_text(policy.get("owner")),
                "owner_role_type": to_text(policy.get("owner_role_type")),
                "comment": to_text(policy.get("comment")),
                "created_on": iso_to_datetime(policy.get("created_on")),
            },
        )

    return transformed


def load_data_policies(
    neo4j_session: neo4j.Session,
    policies: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeDataPolicySchema(),
        policies,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeDataPolicySchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> bool:
    """Sync data governance policies.

    Runs after the schema hierarchy so every containment edge resolves on the first
    pass. ``schemas`` is the already-synced schema listing and is used to report
    policies whose schema is missing from the graph.

    Returns whether every policy kind could be listed. When one could not, the caller
    skips data policy cleanup so previously collected policies are not deleted.
    """
    policies = get(client)
    if policies is None:
        return False

    transformed = transform(policies, client.account_id)
    known_schema_ids = {schema["id"] for schema in schemas}
    unlinked = sum(
        1
        for policy in transformed
        if policy["parent_schema_id"] not in known_schema_ids
    )
    if unlinked:
        logger.warning(
            "%d Snowflake data policies sit in a schema that is not in the graph; "
            "their containment edges are omitted.",
            unlinked,
        )
    logger.info(
        "Loading %d Snowflake data governance policies for account %s.",
        len(transformed),
        client.account_id,
    )
    load_data_policies(
        neo4j_session,
        transformed,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
