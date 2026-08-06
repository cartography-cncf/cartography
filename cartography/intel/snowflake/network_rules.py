"""Snowflake network rules: the reusable network identifier lists policies reference.

Network rules are listed per schema. A 403 or 404 on one schema is recorded as
incomplete rather than fatal, so a collector role missing ``USAGE`` on a single schema
does not cost the whole account.
"""

import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import sf_path_segment
from cartography.intel.snowflake.util import skip_or_raise_http
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.network_rule import SnowflakeNetworkRuleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_schema_network_rules(
    client: SnowflakeClient,
    database_name: str,
    schema_name: str,
) -> list[dict[str, Any]] | None:
    """Network rules of one schema, or None when the role cannot read that schema."""
    try:
        return client.list_all(
            f"/api/v2/databases/{sf_path_segment(database_name)}/schemas/{sf_path_segment(schema_name)}/network-rules",
        )
    except requests.HTTPError as error:
        skip_or_raise_http(error, 403, 404)
        logger.warning(
            "Cannot list network rules of Snowflake schema %s.%s (permission denied); "
            "they will be missing from the graph.",
            database_name,
            schema_name,
        )
        return None


@timeit
def get(
    client: SnowflakeClient, schemas: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], bool]:
    """Return every readable network rule plus whether every schema could be read."""
    rules: list[dict[str, Any]] = []
    complete = True
    for schema in schemas:
        rows = get_schema_network_rules(client, schema["database_name"], schema["name"])
        if rows is None:
            complete = False
            continue
        rules.extend(rows)
    return rules, complete


def transform(rules: list[dict[str, Any]], account_id: str) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for rule in rules:
        database_name = rule["database_name"]
        schema_name = rule["schema_name"]
        name = rule["name"]
        qualified_name = sf_fqn(database_name, schema_name, name)
        value_list = rule.get("value_list") or []
        transformed.append(
            {
                "id": sf_id(account_id, "network_rule", qualified_name),
                "name": name,
                "qualified_name": qualified_name,
                "database_name": database_name,
                "schema_name": schema_name,
                "parent_schema_id": sf_id(
                    account_id, "schema", sf_fqn(database_name, schema_name)
                ),
                "rule_type": rule.get("type"),
                "mode": rule.get("mode"),
                "value_list": value_list,
                "value_count": len(value_list),
                "owner": rule.get("owner"),
                "comment": rule.get("comment"),
                "created_on": iso_to_datetime(rule.get("created_on")),
            },
        )
    return transformed


def load_network_rules(
    neo4j_session: neo4j.Session,
    rules: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeNetworkRuleSchema(),
        rules,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(SnowflakeNetworkRuleSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    schemas: list[dict[str, Any]],
    common_job_parameters: dict,
) -> tuple[list[dict[str, Any]], bool]:
    """Sync network rules, returning them and whether every schema could be read.

    Runs before network policies and external access integrations, whose ALLOWS edges
    resolve against these nodes. The rules themselves are returned because a network
    policy references them by bare name, so the policy sync needs the synced rules to
    resolve those references to ids.
    """
    raw_rules, complete = get(client, schemas)
    rules = transform(raw_rules, client.account_id)
    logger.info(
        "Loading %d Snowflake network rules for account %s.",
        len(rules),
        client.account_id,
    )
    load_network_rules(
        neo4j_session, rules, client.account_id, common_job_parameters["UPDATE_TAG"]
    )
    if not complete:
        logger.warning(
            "Some Snowflake schemas could not be listed; skipping network rule cleanup "
            "so still-valid rules are not deleted.",
        )
    return rules, complete
