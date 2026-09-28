"""Snowflake policy attachments.

A policy object only has an effect once it is attached to something, and the
attachments are not visible on either end's own listing: they live in
``SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES``, which reports every policy kind in
one row shape. That single shape is what makes it worth resolving here rather than
in each policy module.

Reading the view needs ``IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE`` and it lags
reality by up to two hours.
"""

import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.grants import securable_id
from cartography.intel.snowflake.sql_values import to_text
from cartography.intel.snowflake.util import is_sql_unavailable
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.intel.snowflake.util import SnowflakeSqlError
from cartography.intel.snowflake.util import warn_unavailable
from cartography.models.snowflake.policy_reference import (
    SnowflakeAuthenticationPolicyAppliedToMatchLink,
)
from cartography.models.snowflake.policy_reference import (
    SnowflakeDataPolicyAppliedToMatchLink,
)
from cartography.models.snowflake.policy_reference import (
    SnowflakePasswordPolicyAppliedToMatchLink,
)
from cartography.models.snowflake.policy_reference import (
    SnowflakeSessionPolicyAppliedToMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

_POLICY_REFERENCES_STATEMENT = """
SELECT POLICY_ID, POLICY_NAME, POLICY_KIND, POLICY_DB, POLICY_SCHEMA,
       REF_ENTITY_NAME, REF_ENTITY_DOMAIN, REF_DATABASE_NAME, REF_SCHEMA_NAME,
       REF_COLUMN_NAME, REF_ARG_COLUMN_NAMES, POLICY_STATUS, TAG_NAME, TAG_DATABASE,
       TAG_SCHEMA
FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
"""

# POLICY_KIND -> the object-type segment the policy's node id was built with. The
# five data governance kinds collapse onto one label, so they share one segment.
POLICY_KIND_TO_OBJECT_TYPE = {
    "MASKING_POLICY": "data_policy",
    "ROW_ACCESS_POLICY": "data_policy",
    "PROJECTION_POLICY": "data_policy",
    "AGGREGATION_POLICY": "data_policy",
    "JOIN_POLICY": "data_policy",
    "PASSWORD_POLICY": "password_policy",
    "SESSION_POLICY": "session_policy",
    "AUTHENTICATION_POLICY": "authentication_policy",
}

_MATCHLINKS = {
    "data_policy": SnowflakeDataPolicyAppliedToMatchLink(),
    "password_policy": SnowflakePasswordPolicyAppliedToMatchLink(),
    "session_policy": SnowflakeSessionPolicyAppliedToMatchLink(),
    "authentication_policy": SnowflakeAuthenticationPolicyAppliedToMatchLink(),
}


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]] | None:
    """Every policy attachment in the account, or None when unreadable."""
    try:
        return client.run_sql(_POLICY_REFERENCES_STATEMENT)
    except SnowflakeSqlError as error:
        if not is_sql_unavailable(error):
            raise
        warn_unavailable(
            "policy attachments",
            "ACCOUNT_USAGE.POLICY_REFERENCES needs IMPORTED PRIVILEGES ON DATABASE "
            "SNOWFLAKE",
        )
        return None


def transform(
    references: list[dict[str, Any]],
    account_id: str,
) -> tuple[dict[str, list[dict[str, Any]]], int]:
    """Group attachment rows into one edge list per policy kind.

    Returns the edges keyed by the policy's object type, plus the number of rows
    skipped because either the policy kind or the attached object's kind is not
    modelled.

    A masking policy attached to several columns of one table produces one row per
    column but a single edge, so the rows are collapsed deterministically on the
    lowest column name rather than letting an arbitrary row win the merge.
    """
    edges: dict[str, dict[tuple[str, str], dict[str, Any]]] = {
        object_type: {} for object_type in _MATCHLINKS
    }
    skipped = 0

    for reference in sorted(
        references,
        key=lambda row: (
            str(row.get("policy_name") or ""),
            str(row.get("ref_entity_name") or ""),
            str(row.get("ref_column_name") or ""),
        ),
    ):
        policy_kind = reference.get("policy_kind")
        object_type = POLICY_KIND_TO_OBJECT_TYPE.get(str(policy_kind or "").upper())
        if not object_type:
            skipped += 1
            continue

        policy_id = sf_id(
            account_id,
            object_type,
            sf_fqn(
                reference["policy_db"],
                reference["policy_schema"],
                reference["policy_name"],
            ),
        )
        target_id = securable_id(
            {
                "database": to_text(reference.get("ref_database_name")),
                "schema": to_text(reference.get("ref_schema_name")),
                "name": to_text(reference.get("ref_entity_name")),
            },
            to_text(reference.get("ref_entity_domain")),
            account_id,
        )
        if not target_id:
            skipped += 1
            continue

        key = (policy_id, target_id)
        if key in edges[object_type]:
            continue
        edges[object_type][key] = {
            "policy_id": policy_id,
            "securable_id": target_id,
            "ref_entity_domain": to_text(reference.get("ref_entity_domain")),
            "ref_column_name": to_text(reference.get("ref_column_name")),
            "policy_status": to_text(reference.get("policy_status")),
        }

    return {
        object_type: list(pairs.values()) for object_type, pairs in edges.items()
    }, skipped


def load_policy_references(
    neo4j_session: neo4j.Session,
    edges: dict[str, list[dict[str, Any]]],
    account_id: str,
    update_tag: int,
) -> None:
    for object_type, matchlink in _MATCHLINKS.items():
        load_matchlinks(
            neo4j_session,
            matchlink,
            edges[object_type],
            lastupdated=update_tag,
            _sub_resource_label="SnowflakeAccount",
            _sub_resource_id=account_id,
        )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    for matchlink in _MATCHLINKS.values():
        GraphJob.from_matchlink(
            matchlink,
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
    """Sync policy attachments.

    Runs after every policy and every object a policy can be attached to, so the
    edges resolve on the first pass.

    Returns whether the view could be read. When it could not, the caller skips
    attachment cleanup so previously collected attachments are not deleted.
    """
    references = get(client)
    if references is None:
        return False

    edges, skipped = transform(references, client.account_id)
    if skipped:
        logger.info(
            "Skipped %d Snowflake policy attachments whose policy or target is not "
            "modelled.",
            skipped,
        )
    logger.info(
        "Loading %d Snowflake policy attachments for account %s.",
        sum(len(rows) for rows in edges.values()),
        client.account_id,
    )
    load_policy_references(
        neo4j_session,
        edges,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
    return True
