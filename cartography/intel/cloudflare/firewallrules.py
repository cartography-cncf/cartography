import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from cloudflare import Cloudflare

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.cloudflare.firewallrule import CloudflareFirewallRuleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Rules per API page, the documented maximum for the firewall rules API.
_PER_PAGE = 50


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Cloudflare,
    common_job_parameters: Dict[str, Any],
    account_id: str,
    zones: List[Dict[str, Any]],
) -> None:
    # Mirror the DNS record pattern: each zone's rules are loaded as soon as
    # they are fetched, and cleanup runs once after every zone has been loaded,
    # so an account with many zones never holds all rules in memory at once and
    # rules from zones not yet synced in this run are not deleted and recreated.
    for zone in zones:
        rules = transform(get(client, zone["id"]))
        logger.info(
            "Loading %d firewall rules for zone '%s'.",
            len(rules),
            zone["id"],
        )
        load_firewallrules(
            neo4j_session,
            rules,
            account_id,
            zone["id"],
            common_job_parameters["UPDATE_TAG"],
        )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(client: Cloudflare, zone_id: str) -> List[Dict[str, Any]]:
    # The SDK auto-paginates; the API allows up to 50 rules per page.
    # See https://developers.cloudflare.com/api/resources/firewall/subresources/rules/methods/list/
    return [
        rule.to_dict()
        for rule in client.firewall.rules.list(zone_id=zone_id, per_page=_PER_PAGE)
    ]


def transform(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flatten the nested filter object into filter_* properties on the rule so the
    schema can load a single node per API record.
    """
    transformed = []
    for rule in data:
        rule = dict(rule)
        rule_filter = rule.get("filter") or {}
        rule["filter_id"] = rule_filter.get("id")
        rule["filter_description"] = rule_filter.get("description")
        rule["filter_expression"] = rule_filter.get("expression")
        rule["filter_paused"] = rule_filter.get("paused")
        rule["filter_ref"] = rule_filter.get("ref")
        rule.pop("filter", None)
        transformed.append(rule)
    return transformed


def load_firewallrules(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    zone_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        CloudflareFirewallRuleSchema(),
        data,
        lastupdated=update_tag,
        account_id=account_id,
        zone_id=zone_id,
    )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        CloudflareFirewallRuleSchema(), common_job_parameters
    ).run(neo4j_session)
