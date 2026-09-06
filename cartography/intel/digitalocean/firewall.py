import hashlib
import json
import logging
from typing import Any

import neo4j
from pydo import Client

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.digitalocean.util.pagination import get_paginated_list
from cartography.models.digitalocean.firewall import DOFirewallSchema
from cartography.models.digitalocean.firewall_rule import DOFirewallRuleSchema
from cartography.models.digitalocean.ip_range import DOIpRangeSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Client,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync DigitalOcean Cloud Firewalls to Neo4j.

    Droplets must be loaded before this function runs so the PROTECTS
    relationships can be created.
    """
    logger.info("Syncing DigitalOcean Firewalls")

    firewalls_res = get_firewalls(client)
    firewalls, firewall_rules, ip_ranges = transform_firewalls(firewalls_res)

    load_firewalls(
        neo4j_session,
        firewalls,
        account_id,
        update_tag,
    )
    load_ip_ranges(
        neo4j_session,
        ip_ranges,
        account_id,
        update_tag,
    )
    load_firewall_rules(
        neo4j_session,
        firewall_rules,
        account_id,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_firewalls(client: Client) -> list[dict[str, Any]]:
    """Fetch all firewalls from the DigitalOcean API."""
    return get_paginated_list(client.firewalls.list, "firewalls")


@timeit
def transform_firewalls(
    firewalls_res: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Shape API responses for DOFirewallSchema.

    Separates firewall resources from their inbound and outbound rules.
    """
    firewalls: list[dict[str, Any]] = []
    firewall_rules: list[dict[str, Any]] = []
    ip_ranges: list[dict[str, Any]] = []

    for firewall in firewalls_res:
        firewalls.append(
            {
                "id": firewall["id"],
                "name": firewall.get("name"),
                "status": firewall.get("status"),
                "created_at": firewall.get("created_at"),
                "tags": firewall.get("tags"),
                "pending_changes": firewall.get("pending_changes"),
                "droplet_ids": firewall.get("droplet_ids"),
            },
        )

        for direction, rules in (
            ("inbound", firewall.get("inbound_rules", [])),
            ("outbound", firewall.get("outbound_rules", [])),
        ):
            transformed_rules, transformed_ranges = _transform_firewall_rules(
                firewall["id"], direction, rules
            )
            firewall_rules.extend(transformed_rules)
            ip_ranges.extend(transformed_ranges)

    return firewalls, firewall_rules, ip_ranges


def _transform_firewall_rules(
    firewall_id: str,
    direction: str,
    rules: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selector_key = "sources" if direction == "inbound" else "destinations"
    transformed_rules: list[dict[str, Any]] = []
    ip_ranges: list[dict[str, Any]] = []
    ip_range_ids: set[str] = set()

    for rule in rules:
        selectors = rule.get(selector_key, {})
        protocol = rule["protocol"]
        ports = rule.get("ports")
        fromport, toport = _parse_port_range(protocol, ports)
        canonical_rule = {
            "direction": direction,
            "protocol": protocol,
            "ports": ports,
            "action": rule.get("action"),
            "selectors": _canonicalize_selectors(selectors),
        }
        serialized_rule = json.dumps(
            canonical_rule,
            separators=(",", ":"),
            sort_keys=True,
        )

        # Use a hash of the serialized rule to create a unique ID for the rule.
        rule_hash = hashlib.sha256(serialized_rule.encode()).hexdigest()[:16]
        ip_range_raw = selectors.get("addresses", [])

        for address in ip_range_raw:
            if address not in ip_range_ids:
                ip_ranges.append(
                    {
                        "id": address,
                        "range": address,
                    }
                )
                ip_range_ids.add(address)

        transformed_rules.append(
            {
                "id": f"{firewall_id}/{rule_hash}",
                "firewall_id": firewall_id,
                "direction": direction,
                "protocol": protocol,
                "ports": ports,
                "fromport": fromport,
                "toport": toport,
                "action": rule.get("action"),
                "source_addresses": ip_range_raw if direction == "inbound" else None,
                "destination_addresses": (
                    ip_range_raw if direction == "outbound" else None
                ),
                "source_tags": (
                    selectors.get("tags") if direction == "inbound" else None
                ),
                "destination_tags": (
                    selectors.get("tags") if direction == "outbound" else None
                ),
                "source_droplet_ids": (
                    selectors.get("droplet_ids") if direction == "inbound" else None
                ),
                "destination_droplet_ids": (
                    selectors.get("droplet_ids") if direction == "outbound" else None
                ),
                "source_load_balancer_uids": (
                    selectors.get("load_balancer_uids")
                    if direction == "inbound"
                    else None
                ),
                "destination_load_balancer_uids": (
                    selectors.get("load_balancer_uids")
                    if direction == "outbound"
                    else None
                ),
                "source_kubernetes_ids": (
                    selectors.get("kubernetes_ids") if direction == "inbound" else None
                ),
                "destination_kubernetes_ids": (
                    selectors.get("kubernetes_ids") if direction == "outbound" else None
                ),
            },
        )

    return transformed_rules, ip_ranges


def _parse_port_range(
    protocol: str,
    ports: str | None,
) -> tuple[int | None, int | None]:
    """Normalize a DigitalOcean port string into inclusive numeric bounds."""
    if protocol not in {"tcp", "udp"}:
        return None, None

    if ports == "0":
        # DigitalOcean uses "0" to mean every TCP or UDP port.
        return 0, 65535

    if ports is None:
        return None, None

    if "-" in ports:
        fromport, toport = ports.split("-", maxsplit=1)
        return int(fromport), int(toport)

    port = int(ports)
    return port, port


def _canonicalize_selectors(selectors: dict[str, Any]) -> dict[str, Any]:
    return {
        key: sorted(value, key=str) if isinstance(value, list) else value
        for key, value in selectors.items()
    }


@timeit
def load_firewalls(
    neo4j_session: neo4j.Session,
    firewalls: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    """Load firewalls and their account/Droplet relationships."""
    load(
        neo4j_session,
        DOFirewallSchema(),
        firewalls,
        lastupdated=update_tag,
        ACCOUNT_ID=str(account_id),
    )


@timeit
def load_firewall_rules(
    neo4j_session: neo4j.Session,
    firewall_rules: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    """Load DigitalOcean firewall rules and their parent relationships."""
    load(
        neo4j_session,
        DOFirewallRuleSchema(),
        firewall_rules,
        lastupdated=update_tag,
        ACCOUNT_ID=str(account_id),
    )


@timeit
def load_ip_ranges(
    neo4j_session: neo4j.Session,
    ip_ranges: list[dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    """Load IP address and CIDR selectors before their firewall-rule edges."""
    load(
        neo4j_session,
        DOIpRangeSchema(),
        ip_ranges,
        lastupdated=update_tag,
        ACCOUNT_ID=str(account_id),
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """Remove stale account-scoped firewall data."""
    GraphJob.from_node_schema(
        DOFirewallSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DOFirewallRuleSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DOIpRangeSchema(),
        common_job_parameters,
    ).run(neo4j_session)
