from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.ruleset import CloudflareRulesetSchema
from cartography.models.cloudflare.rulesetrule import CloudflareRulesetRuleSchema
from cartography.util import timeit

# Phases whose rules decide whether traffic is allowed, blocked or challenged.
# The other phases configure caching, transforms, redirects and custom errors,
# which are not firewall behaviour.
# See https://developers.cloudflare.com/ruleset-engine/reference/phases-list/
_SECURITY_PHASES = frozenset(
    {
        "ddos_l4",
        "ddos_l7",
        "http_ratelimit",
        "http_request_firewall_custom",
        "http_request_firewall_managed",
        "http_request_sbfm",
        "http_response_firewall_managed",
        # Magic Firewall, the network-layer equivalent for Magic Transit.
        "magic_transit",
        "magic_transit_managed",
        "magic_transit_ratelimit",
        # magic_transit_ids_managed is deliberately absent: Magic Firewall IDS
        # detects and alerts on traffic without deciding whether it passes.
    }
)

# Cloudflare-provided rulesets hold hundreds of vendor-owned rules that are not
# customer configuration. Their contents are skipped; the `execute` rule that
# turns a managed ruleset on is ingested from the customer's own ruleset.
_VENDOR_RULESET_KIND = "managed"

_ACCOUNT_SCOPE = "account"
_ZONE_SCOPE = "zone"

# The phase entry point rulesets of a scope: `root` at the account level, `zone`
# at the zone level. They are the rulesets Cloudflare evaluates directly, and the
# only place a rule can deploy another ruleset from.
_ENTRY_POINT_KIND_BY_SCOPE = {_ACCOUNT_SCOPE: "root", _ZONE_SCOPE: _ZONE_SCOPE}

_EXECUTE_ACTION = "execute"


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    account_id: str,
    zones: List[Dict[str, Any]],
) -> None:
    # Rulesets deploy at two levels: an account-level ruleset covers every zone
    # in the account, a zone-level one covers a single zone. Both are read.
    # See https://developers.cloudflare.com/ruleset-engine/managed-rulesets/deploy-managed-ruleset/
    sync_scope(
        neo4j_session,
        client,
        account_id,
        None,
        common_job_parameters["UPDATE_TAG"],
    )
    # Rulesets are scoped to the account (the tenant), so both cleanups run once
    # after every scope has been loaded: cleaning up per zone would delete the
    # rulesets of zones not yet synced in this run.
    for zone in zones:
        sync_scope(
            neo4j_session,
            client,
            account_id,
            zone["id"],
            common_job_parameters["UPDATE_TAG"],
        )
    cleanup(neo4j_session, common_job_parameters)


def sync_scope(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    account_id: str,
    zone_id: str | None,
    update_tag: int,
) -> None:
    """
    Load the rulesets deployed in a single scope, and the rules of the
    customer-authored ones. A `zone_id` of None reads the account level.

    The listing endpoint returns every ruleset *available* at the scope rather
    than the deployed ones: the Cloudflare-provided rulesets are listed in every
    account and every zone, a zone listing also carries the account-level rulesets
    one may want to deploy to that zone, and creating a custom ruleset does not
    activate it. What deploys a ruleset is an enabled rule with the `execute`
    action in one of the scope's phase entry point rulesets, so the deployments of
    a scope are its entry points plus what those enable.
    See https://developers.cloudflare.com/ruleset-engine/managed-rulesets/deploy-managed-ruleset/
    """
    scope = _ZONE_SCOPE if zone_id else _ACCOUNT_SCOPE
    available = get_rulesets(client, account_id, zone_id)
    entry_points = [
        ruleset
        for ruleset in available
        if ruleset["kind"] == _ENTRY_POINT_KIND_BY_SCOPE[scope]
    ]

    # The entry point rules come first: they are what names the rulesets deployed
    # in this scope. Keyed by ruleset API ID, since that is what an execute rule
    # refers to.
    rules_by_ruleset: Dict[str, List[Dict[str, Any]]] = {
        ruleset["id"]: get_ruleset_rules(client, account_id, zone_id, ruleset["id"])
        for ruleset in entry_points
    }
    entry_point_ids = {ruleset["id"] for ruleset in entry_points}
    executed_ids = executed_ruleset_ids(
        [rule for rules in rules_by_ruleset.values() for rule in rules]
    )
    executed = [
        ruleset
        for ruleset in available
        if ruleset["id"] in executed_ids and ruleset["id"] not in entry_point_ids
    ]

    load_rulesets(
        neo4j_session,
        transform_rulesets(entry_points + executed, account_id, zone_id),
        account_id,
        zone_id,
        update_tag,
    )

    for ruleset in executed:
        # A vendor-owned ruleset holds hundreds of rules that are not customer
        # configuration. The customer's choice is the execute rule that turns it
        # on, and that one lives in an entry point already read above.
        if ruleset["kind"] == _VENDOR_RULESET_KIND:
            continue
        rules_by_ruleset[ruleset["id"]] = get_ruleset_rules(
            client, account_id, zone_id, ruleset["id"]
        )

    for ruleset_id, rules in rules_by_ruleset.items():
        # The rules hang off the deployment, not off the shared API ID.
        ruleset_deployment_id = deployment_id(account_id, zone_id, ruleset_id)
        load_ruleset_rules(
            neo4j_session,
            transform_ruleset_rules(
                rules,
                account_id,
                zone_id,
                ruleset_deployment_id,
            ),
            account_id,
            ruleset_deployment_id,
            update_tag,
        )


def executed_ruleset_ids(rules: List[Dict[str, Any]]) -> set[str]:
    """
    Return the API IDs of the rulesets the given rules deploy: the target of every
    enabled `execute` rule. A disabled rule deploys nothing, so its target is not
    reported as running in the scope.
    """
    executed = set()
    for rule in rules:
        if rule.get("action") != _EXECUTE_ACTION or not rule.get("enabled"):
            continue
        target = (rule.get("action_parameters") or {}).get("id")
        if target:
            executed.add(target)
    return executed


@timeit
def get_rulesets(
    client: Cloudflare, account_id: str, zone_id: str | None
) -> List[Dict[str, Any]]:
    # The endpoint takes an account ID or a zone ID, never both.
    scope_params = {"zone_id": zone_id} if zone_id else {"account_id": account_id}
    return [ruleset.to_dict() for ruleset in client.rulesets.list(**scope_params)]


@timeit
def get_ruleset_rules(
    client: Cloudflare, account_id: str, zone_id: str | None, ruleset_id: str
) -> List[Dict[str, Any]]:
    # The list endpoint returns ruleset metadata only; the rules of a ruleset
    # require fetching the ruleset itself.
    scope_params = {"zone_id": zone_id} if zone_id else {"account_id": account_id}
    ruleset = client.rulesets.get(ruleset_id, **scope_params)
    # The SDK types `rules` as required, but the API omits it for a ruleset with
    # no rules configured, so it arrives as None.
    return [rule.to_dict() for rule in ruleset.rules or []]


def deployment_id(account_id: str, zone_id: str | None, ruleset_id: str) -> str:
    """
    Build the graph ID of a ruleset deployment.

    A Cloudflare-provided ruleset carries the same API ID in every zone and
    account that deploys it, so the ID is qualified with the scope it applies to.
    Zone IDs and account IDs are both globally unique, so the two forms cannot
    collide.
    """
    return f"{zone_id or account_id}/{ruleset_id}"


def transform_rulesets(
    rulesets: List[Dict[str, Any]],
    account_id: str,
    zone_id: str | None,
) -> List[Dict[str, Any]]:
    """
    Qualify the ruleset IDs with their deployment scope, keeping the raw API ID,
    record the deployment level, and flag the access-control rulesets. The flag
    is a string because the conditional ontology label matches node properties by
    exact string equality.
    """
    transformed = []
    for ruleset in rulesets:
        row = ruleset.copy()
        row["ruleset_id"] = ruleset["id"]
        row["id"] = deployment_id(account_id, zone_id, ruleset["id"])
        row["scope"] = _ZONE_SCOPE if zone_id else _ACCOUNT_SCOPE
        row["security_ruleset"] = (
            "true" if ruleset["phase"] in _SECURITY_PHASES else "false"
        )
        transformed.append(row)
    return transformed


def transform_ruleset_rules(
    rules: List[Dict[str, Any]],
    account_id: str,
    zone_id: str | None,
    ruleset_deployment_id: str,
) -> List[Dict[str, Any]]:
    """
    Qualify the rule IDs with the deployment they were read from, and resolve the
    target of an `execute` rule to a single ruleset deployment.

    `action_parameters.id` is the executed ruleset's API ID, which every
    deployment of that ruleset shares, so it cannot name a target on its own. A
    rule executes the ruleset in its own scope, so the target is resolved in the
    scope the rule was read from.
    """
    transformed = []
    for rule in rules:
        row = rule.copy()
        row["rule_id"] = rule["id"]
        row["id"] = f"{ruleset_deployment_id}/{rule['id']}"
        # `action_parameters` is optional, and a rule that carries none comes back
        # with the key absent or explicitly null, as executed_ruleset_ids() sees.
        executed_ruleset_id = (rule.get("action_parameters") or {}).get("id")
        row["executed_deployment_id"] = (
            deployment_id(account_id, zone_id, executed_ruleset_id)
            if executed_ruleset_id
            else None
        )
        transformed.append(row)
    return transformed


def load_rulesets(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    zone_id: str | None,
    update_tag: int,
) -> None:
    # A null zone_id leaves the HAS_RULESET edge unmatched, which is what an
    # account-level ruleset needs: it belongs to the account, not to a zone.
    load(
        neo4j_session,
        CloudflareRulesetSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
        zone_id=zone_id,
    )


def load_ruleset_rules(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    ruleset_id: str,
    update_tag: int,
) -> None:
    # `ruleset_id` is the deployment ID built by deployment_id(), not the raw API
    # ID, so the rules attach to the deployment they were read from.
    load(
        neo4j_session,
        CloudflareRulesetRuleSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
        ruleset_id=ruleset_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(CloudflareRulesetRuleSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(CloudflareRulesetSchema(), common_job_parameters).run(
        neo4j_session
    )
