import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.snowflake.names import split_qualified_name
from cartography.intel.snowflake.util import iso_to_datetime
from cartography.intel.snowflake.util import sf_fqn
from cartography.intel.snowflake.util import sf_id
from cartography.intel.snowflake.util import SnowflakeClient
from cartography.models.snowflake.network_policy import SnowflakeNetworkPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# A policy whose allowed list contains this places no effective restriction on
# IPv4 traffic, which is worth flagging because it still satisfies Snowflake's
# "a network policy is required" check for programmatic access tokens.
_UNRESTRICTED_IPV4 = "0.0.0.0/0"


@timeit
def get(client: SnowflakeClient) -> list[dict[str, Any]]:
    return client.list_all("/api/v2/network-policies")


def _rule_ids(
    references: Any,
    rule_ids_by_name: dict[str, list[str]],
    account_id: str,
) -> list[str]:
    """Resolve referenced network rule names to network rule node ids.

    Snowflake reports a referenced rule by bare name (``PLANT_EGRESS``), not
    qualified, even though a network rule is a schema-level object. A network policy
    is account-level, so the payload alone cannot say which schema the rule lives
    in; the reference is therefore resolved against the rules already synced, keyed
    by name.

    A name that matches no rule, or more than one rule in different schemas, yields
    no edge rather than a possibly wrong one. A fully-qualified reference is still
    accepted, since Snowflake has used that form too.
    """
    if not references:
        return []
    if isinstance(references, str):
        references = [
            reference.strip()
            for reference in references.split(",")
            if reference.strip()
        ]
    resolved: list[str] = []
    for reference in references:
        # Snowflake may return either a bare string or a {name: ...} object.
        name = (
            reference.get("fullyQualifiedName") or reference.get("name")
            if isinstance(reference, dict)
            else reference
        )
        if not name:
            continue
        parts = split_qualified_name(str(name))
        if len(parts) == 3:
            resolved.append(sf_id(account_id, "network_rule", sf_fqn(*parts)))
            continue
        candidates = rule_ids_by_name.get(str(name).upper(), [])
        if len(candidates) == 1:
            resolved.append(candidates[0])
        elif not candidates:
            logger.debug(
                "Snowflake network rule %s is referenced by a network policy but was "
                "not synced; drawing no edge for it.",
                name,
            )
        else:
            logger.warning(
                "Snowflake network rule name %s is ambiguous across %d schemas; "
                "drawing no edge rather than guessing which one the policy means.",
                name,
                len(candidates),
            )
    return resolved


def transform(
    policies: list[dict[str, Any]],
    account_network_policy: str | None,
    network_rules: list[dict[str, Any]],
    account_id: str,
) -> list[dict[str, Any]]:
    """Shape network policies, marking whichever one is in force account-wide.

    ``account_network_policy`` is the value of the account's ``NETWORK_POLICY``
    parameter. Only the matching policy gets ``attached_account_id`` set, which is
    what makes the account's ``GOVERNED_BY`` edge form for that policy alone; the
    field stays null on every other policy so no spurious edge appears.
    """
    # Referenced rules arrive as bare names, so index the synced rules by name to
    # resolve them.
    rule_ids_by_name: dict[str, list[str]] = {}
    for rule in network_rules:
        rule_ids_by_name.setdefault(str(rule["name"]).upper(), []).append(rule["id"])

    transformed: list[dict[str, Any]] = []
    for policy in policies:
        name = policy["name"]
        allowed_ip_list = policy.get("allowed_ip_list") or []
        blocked_ip_list = policy.get("blocked_ip_list") or []
        is_account_policy = (
            account_network_policy is not None and account_network_policy == name
        )
        transformed.append(
            {
                "id": sf_id(account_id, "network_policy", name),
                "name": name,
                "allowed_ip_list": allowed_ip_list,
                "blocked_ip_list": blocked_ip_list,
                "allows_all_ipv4": _UNRESTRICTED_IPV4 in allowed_ip_list,
                "allowed_ip_count": len(allowed_ip_list),
                "blocked_ip_count": len(blocked_ip_list),
                "allowed_network_rule_ids": _rule_ids(
                    policy.get("allowed_network_rule_list"),
                    rule_ids_by_name,
                    account_id,
                ),
                "blocked_network_rule_ids": _rule_ids(
                    policy.get("blocked_network_rule_list"),
                    rule_ids_by_name,
                    account_id,
                ),
                "comment": policy.get("comment"),
                "owner": policy.get("owner") or None,
                "created_on": iso_to_datetime(policy.get("created_on")),
                "attached_to_account": is_account_policy,
                "attached_account_id": account_id if is_account_policy else None,
            },
        )
    return transformed


def load_network_policies(
    neo4j_session: neo4j.Session,
    policies: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SnowflakeNetworkPolicySchema(),
        policies,
        lastupdated=update_tag,
        ACCOUNT_ID=account_id,
    )


def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        SnowflakeNetworkPolicySchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: SnowflakeClient,
    account_network_policy: str | None,
    network_rules: list[dict[str, Any]],
    common_job_parameters: dict,
) -> None:
    """Sync network policies.

    Runs after network rules, so the ALLOWS and BLOCKS edges resolve against rule
    nodes already in the graph, and before users, whose GOVERNED_BY edge points at
    a policy.
    """
    policies = transform(
        get(client), account_network_policy, network_rules, client.account_id
    )
    logger.info(
        "Loading %d Snowflake network policies for account %s.",
        len(policies),
        client.account_id,
    )
    load_network_policies(
        neo4j_session,
        policies,
        client.account_id,
        common_job_parameters["UPDATE_TAG"],
    )
