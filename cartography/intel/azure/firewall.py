import json
import logging
import re
from typing import Any

import neo4j
from azure.core.exceptions import HttpResponseError
from azure.mgmt.network import NetworkManagementClient

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.azure.util.common import copy_properties
from cartography.intel.azure.util.common import rename_keys
from cartography.intel.azure.util.credentials import Credentials
from cartography.models.azure.firewall.azure_firewall import AzureFirewallSchema
from cartography.models.azure.firewall.firewall_policy import AzureFirewallPolicySchema
from cartography.models.azure.firewall.ip_configuration import (
    AzureFirewallIPConfigurationSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)


# azure-mgmt-network 31+ serializes `as_dict()` in ARM wire format: resource-specific
# fields sit under `properties` with camelCase names. The transforms read flat
# snake_case keys, so each payload is normalized back to that shape first.
_FIREWALL_PROPERTY_MAP = {
    "provisioning_state": ("provisioningState",),
    "threat_intel_mode": ("threatIntelMode",),
    "sku": ("sku",),
    "firewall_policy": ("firewallPolicy",),
    "virtual_hub": ("virtualHub",),
    "ip_configurations": ("ipConfigurations",),
    "management_ip_configuration": ("managementIpConfiguration",),
    "hub_ip_addresses": ("hubIPAddresses",),
    "ip_groups": ("ipGroups",),
    "autoscale_configuration": ("autoscaleConfiguration",),
    "additional_properties": ("additionalProperties",),
    "network_rule_collections": ("networkRuleCollections",),
    "application_rule_collections": ("applicationRuleCollections",),
    "nat_rule_collections": ("natRuleCollections",),
}
_AUTOSCALE_KEY_MAP = {"min_capacity": "minCapacity", "max_capacity": "maxCapacity"}
_FIREWALL_POLICY_PROPERTY_MAP = {
    "provisioning_state": ("provisioningState",),
    "threat_intel_mode": ("threatIntelMode",),
    "size": ("size",),
    "sku": ("sku",),
    "base_policy": ("basePolicy",),
    "dns_settings": ("dnsSettings",),
    "sql": ("sql",),
    "snat": ("snat",),
    "explicit_proxy": ("explicitProxy",),
    "intrusion_detection": ("intrusionDetection",),
    "insights": ("insights",),
    "transport_security": ("transportSecurity",),
    "threat_intel_whitelist": ("threatIntelWhitelist",),
    "rule_collection_groups": ("ruleCollectionGroups",),
    "child_policies": ("childPolicies",),
    "firewalls": ("firewalls",),
}
_POLICY_NESTED_KEY_MAPS = {
    "dns_settings": {
        "enable_proxy": "enableProxy",
        "require_proxy_for_network_rules": "requireProxyForNetworkRules",
    },
    "sql": {"allow_sql_redirect": "allowSqlRedirect"},
    "snat": {
        "private_ranges": "privateRanges",
        "auto_learn_private_ranges": "autoLearnPrivateRanges",
    },
    "explicit_proxy": {
        "enable_explicit_proxy": "enableExplicitProxy",
        "http_port": "httpPort",
        "https_port": "httpsPort",
        "enable_pac_file": "enablePacFile",
        "pac_file_port": "pacFilePort",
        "pac_file": "pacFile",
    },
    "insights": {"is_enabled": "isEnabled", "retention_days": "retentionDays"},
    "transport_security": {"certificate_authority": "certificateAuthority"},
    "threat_intel_whitelist": {"ip_addresses": "ipAddresses"},
}
_INTRUSION_DETECTION_CONFIGURATION_KEY_MAP = {
    "signature_overrides": "signatureOverrides",
    "bypass_traffic_settings": "bypassTrafficSettings",
    "private_ranges": "privateRanges",
}
_CERTIFICATE_AUTHORITY_KEY_MAP = {"key_vault_secret_id": "keyVaultSecretId"}


# Rule collections, rule collection groups, IP configurations and IP groups are
# stored as JSON, so they keep the flattened snake_case shape of the older SDKs
# rather than one that depends on the installed SDK version. Their nested rule
# types are polymorphic, so a generic conversion replaces per-type key maps; the
# camelCase-to-snake rule matches the SDK's own attribute names for every model
# in these payloads.
_CAMEL_CASE_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_FREE_FORM_KEYS = {"tags"}


def _to_flattened_snake_case(value: Any) -> Any:
    if isinstance(value, list):
        return [_to_flattened_snake_case(item) for item in value]
    if not isinstance(value, dict):
        return value
    flattened = {key: item for key, item in value.items() if key != "properties"}
    properties = value.get("properties")
    if isinstance(properties, dict):
        for key, item in properties.items():
            flattened.setdefault(key, item)
    return {
        _CAMEL_CASE_BOUNDARY.sub("_", key).lower(): (
            item if key in _FREE_FORM_KEYS else _to_flattened_snake_case(item)
        )
        for key, item in flattened.items()
    }


def _normalize_firewall(firewall: dict[str, Any]) -> dict[str, Any]:
    copy_properties(firewall, _FIREWALL_PROPERTY_MAP)
    rename_keys(firewall, {"extended_location": "extendedLocation"})
    for key in (
        "ip_configurations",
        "management_ip_configuration",
        "network_rule_collections",
        "application_rule_collections",
        "nat_rule_collections",
    ):
        if firewall.get(key):
            firewall[key] = _to_flattened_snake_case(firewall[key])
    rename_keys(firewall.get("autoscale_configuration"), _AUTOSCALE_KEY_MAP)
    hub = rename_keys(
        firewall.get("hub_ip_addresses"), {"private_ip_address": "privateIPAddress"}
    )
    # The wire shape nests the hub's public IPs as {"addresses": [...], "count": n}.
    if isinstance(hub, dict) and "public_ip_addresses" not in hub:
        hub["public_ip_addresses"] = (hub.get("publicIPs") or {}).get("addresses")
    return firewall


def _normalize_firewall_policy(policy: dict[str, Any]) -> dict[str, Any]:
    copy_properties(policy, _FIREWALL_POLICY_PROPERTY_MAP)
    for key, key_map in _POLICY_NESTED_KEY_MAPS.items():
        rename_keys(policy.get(key), key_map)
    intrusion_detection = policy.get("intrusion_detection")
    if isinstance(intrusion_detection, dict):
        rename_keys(
            intrusion_detection.get("configuration"),
            _INTRUSION_DETECTION_CONFIGURATION_KEY_MAP,
        )
    transport_security = policy.get("transport_security")
    if isinstance(transport_security, dict):
        rename_keys(
            transport_security.get("certificate_authority"),
            _CERTIFICATE_AUTHORITY_KEY_MAP,
        )
    return policy


@timeit
def get_client(
    credentials: Credentials, subscription_id: str
) -> NetworkManagementClient:
    """
    Create Azure Network Management client
    """
    return NetworkManagementClient(credentials.credential, subscription_id)


@timeit
def get_firewalls(client: NetworkManagementClient) -> list[dict[str, Any]]:
    """
    Get all Azure Firewalls in the subscription.

    :raises HttpResponseError: If the Azure API request fails (e.g., auth errors, network issues)
    :return: List of firewall dictionaries
    """
    firewalls = list(client.azure_firewalls.list_all())
    return [fw.as_dict() for fw in firewalls]


@timeit
def get_firewall_policies(client: NetworkManagementClient) -> list[dict[str, Any]]:
    """
    Get all Azure Firewall Policies in the subscription.

    :raises HttpResponseError: If the Azure API request fails (e.g., auth errors, network issues)
    :return: List of firewall policy dictionaries
    """
    policies = list(client.firewall_policies.list_all())
    return [policy.as_dict() for policy in policies]


@timeit
def get_firewall_policy_rule_groups(
    client: NetworkManagementClient,
    policy_id: str,
) -> list[dict[str, Any]]:
    """
    Get rule collection groups for a specific firewall policy
    This contains the actual security rules (network, application, NAT rules)
    """
    try:
        # Parse resource group and policy name from ID
        # Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/firewallPolicies/{name}
        parts = policy_id.split("/")
        resource_group = parts[4]
        policy_name = parts[-1]

        rule_groups = list(
            client.firewall_policy_rule_collection_groups.list(
                resource_group, policy_name
            )
        )
        return [rg.as_dict() for rg in rule_groups]
    except HttpResponseError as e:
        logger.warning("Failed to retrieve rule groups for policy %s: %s", policy_id, e)
        return []
    except (IndexError, ValueError) as e:
        logger.warning("Failed to parse policy ID %s: %s", policy_id, e)
        return []


@timeit
def get_ip_groups(client: NetworkManagementClient) -> list[dict[str, Any]]:
    """
    Get IP Groups - collections of IP addresses/ranges used in firewall rules
    Critical for understanding what IPs are allowed/blocked
    """
    try:
        ip_groups = list(client.ip_groups.list())
        return [ipg.as_dict() for ipg in ip_groups]
    except HttpResponseError as e:
        logger.warning("Failed to retrieve IP Groups: %s", e)
        return []


def transform_firewalls(firewalls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform Azure Firewall data for ingestion
    Real Azure API returns flat structure (not nested under properties)
    """
    result = []
    for fw in firewalls:
        # Real API has flat structure, not nested under "properties"
        sku = fw.get("sku", {})
        additional_props = fw.get("additional_properties", {})
        hub_ip_addresses = fw.get("hub_ip_addresses", {})

        transformed = {
            # Required fields
            "id": fw["id"],
            "name": fw.get("name"),
            "location": fw.get("location"),
            "type": fw.get("type"),
            # Optional standard fields
            "etag": fw.get("etag"),
            "zones": json.dumps(fw.get("zones")) if fw.get("zones") else None,
            "tags": json.dumps(fw.get("tags")) if fw.get("tags") else None,
            # Provisioning and configuration
            "provisioning_state": fw.get("provisioning_state"),
            "threat_intel_mode": fw.get("threat_intel_mode"),
            # SKU information
            "sku_name": sku.get("name"),
            "sku_tier": sku.get("tier"),
            # Policy and virtual hub references
            "firewall_policy_id": fw.get("firewall_policy", {}).get("id"),
            "virtual_hub_id": fw.get("virtual_hub", {}).get("id"),
            # VNet ID from first IP configuration's subnet
            "vnet_id": (
                fw.get("ip_configurations", [{}])[0]
                .get("subnet", {})
                .get("id", "")
                .rsplit("/subnets/", 1)[0]
                if fw.get("ip_configurations")
                and fw.get("ip_configurations", [{}])[0].get("subnet", {}).get("id")
                else None
            ),
            # Extended location
            "extended_location_name": fw.get("extended_location", {}).get("name"),
            "extended_location_type": fw.get("extended_location", {}).get("type"),
            # Hub IP addressing
            "hub_private_ip_address": hub_ip_addresses.get("private_ip_address"),
            "hub_public_ip_count": (
                len(hub_ip_addresses.get("public_ip_addresses", []))
                if hub_ip_addresses.get("public_ip_addresses")
                else 0
            ),
            # Capacity and scaling
            "ip_groups_count": (
                len(fw.get("ip_groups", [])) if fw.get("ip_groups") else 0
            ),
            "autoscale_min_capacity": fw.get("autoscale_configuration", {}).get(
                "min_capacity"
            ),
            "autoscale_max_capacity": fw.get("autoscale_configuration", {}).get(
                "max_capacity"
            ),
            # Additional properties as JSON
            "additional_properties": (
                json.dumps(additional_props) if additional_props else None
            ),
            # Management IP configuration
            "has_management_ip": fw.get("management_ip_configuration") is not None,
            # IP Configurations - security critical
            "ip_configurations": (
                json.dumps(fw.get("ip_configurations"))
                if fw.get("ip_configurations")
                else None
            ),
            "management_ip_configuration": (
                json.dumps(fw.get("management_ip_configuration"))
                if fw.get("management_ip_configuration")
                else None
            ),
            # Rule Collections - security critical (ports, protocols, addresses)
            "network_rule_collections": (
                json.dumps(fw.get("network_rule_collections"))
                if fw.get("network_rule_collections")
                else None
            ),
            "application_rule_collections": (
                json.dumps(fw.get("application_rule_collections"))
                if fw.get("application_rule_collections")
                else None
            ),
            "nat_rule_collections": (
                json.dumps(fw.get("nat_rule_collections"))
                if fw.get("nat_rule_collections")
                else None
            ),
            # IP Groups detail - actual IP addresses/ranges used in rules
            "ip_groups_detail": (
                json.dumps(fw.get("_ip_groups_detail"))
                if fw.get("_ip_groups_detail")
                else None
            ),
            # Counts
            "ip_configuration_count": len(fw.get("ip_configurations", [])),
            "application_rule_collection_count": len(
                fw.get("application_rule_collections", [])
            ),
            "nat_rule_collection_count": len(fw.get("nat_rule_collections", [])),
            "network_rule_collection_count": len(
                fw.get("network_rule_collections", [])
            ),
        }

        result.append(transformed)

    return result


def transform_firewall_policies(policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform Azure Firewall Policy data for ingestion
    Real Azure API returns flat structure (not nested under properties)
    """
    result = []
    for policy in policies:
        # Real API has flat structure, not nested under "properties"
        sku = policy.get("sku", {})
        dns_settings = policy.get("dns_settings", {})
        sql_settings = policy.get("sql", {})
        snat_settings = policy.get("snat", {})
        explicit_proxy = policy.get("explicit_proxy", {})
        intrusion_detection = policy.get("intrusion_detection", {})
        intrusion_config = (
            intrusion_detection.get("configuration", {}) if intrusion_detection else {}
        )
        insights = policy.get("insights", {})
        transport_security = policy.get("transport_security", {})
        cert_authority = (
            transport_security.get("certificate_authority", {})
            if transport_security
            else {}
        )
        threat_intel_whitelist = policy.get("threat_intel_whitelist", {})

        transformed = {
            # Required fields
            "id": policy["id"],
            "name": policy.get("name"),
            "location": policy.get("location"),
            "type": policy.get("type"),
            # Optional standard fields
            "etag": policy.get("etag"),
            "tags": json.dumps(policy.get("tags")) if policy.get("tags") else None,
            # Provisioning and configuration
            "provisioning_state": policy.get("provisioning_state"),
            "threat_intel_mode": policy.get("threat_intel_mode"),
            "size": policy.get("size"),
            # SKU
            "sku_tier": sku.get("tier"),
            # Parent policy
            "base_policy_id": policy.get("base_policy", {}).get("id"),
            # DNS Settings
            "dns_enable_proxy": dns_settings.get("enable_proxy"),
            "dns_require_proxy_for_network_rules": dns_settings.get(
                "require_proxy_for_network_rules",
            ),
            "dns_servers": (
                json.dumps(dns_settings.get("servers"))
                if dns_settings.get("servers")
                else None
            ),
            # SQL Settings
            "sql_allow_sql_redirect": sql_settings.get("allow_sql_redirect"),
            # SNAT Settings - security critical (defines what gets NATted)
            "snat_private_ranges": (
                json.dumps(snat_settings.get("private_ranges"))
                if snat_settings.get("private_ranges")
                else None
            ),
            "snat_auto_learn_private_ranges": snat_settings.get(
                "auto_learn_private_ranges",
            ),
            # Explicit Proxy Settings - security critical (proxy ports)
            "explicit_proxy_enable": explicit_proxy.get("enable_explicit_proxy"),
            "explicit_proxy_http_port": explicit_proxy.get("http_port"),
            "explicit_proxy_https_port": explicit_proxy.get("https_port"),
            "explicit_proxy_enable_pac_file": explicit_proxy.get("enable_pac_file"),
            "explicit_proxy_pac_file_port": explicit_proxy.get("pac_file_port"),
            "explicit_proxy_pac_file": explicit_proxy.get("pac_file"),
            # Intrusion Detection - security critical
            "intrusion_detection_mode": (
                intrusion_detection.get("mode") if intrusion_detection else None
            ),
            "intrusion_detection_profile": (
                intrusion_detection.get("profile") if intrusion_detection else None
            ),
            # Insights
            "insights_is_enabled": insights.get("is_enabled") if insights else None,
            "insights_retention_days": (
                insights.get("retention_days") if insights else None
            ),
            # Transport Security
            "transport_security_ca_name": cert_authority.get("name"),
            "transport_security_key_vault_secret_id": cert_authority.get(
                "key_vault_secret_id",
            ),
            # Threat Intel Whitelist - security critical (bypass rules)
            "threat_intel_whitelist_ip_addresses": (
                json.dumps(threat_intel_whitelist.get("ip_addresses"))
                if threat_intel_whitelist.get("ip_addresses")
                else None
            ),
            "threat_intel_whitelist_fqdns": (
                json.dumps(threat_intel_whitelist.get("fqdns"))
                if threat_intel_whitelist.get("fqdns")
                else None
            ),
            # Intrusion Detection Configuration - security critical (bypass traffic, signature overrides)
            "intrusion_detection_signature_overrides": (
                json.dumps(intrusion_config.get("signature_overrides"))
                if intrusion_config.get("signature_overrides")
                else None
            ),
            "intrusion_detection_bypass_traffic": (
                json.dumps(intrusion_config.get("bypass_traffic_settings"))
                if intrusion_config.get("bypass_traffic_settings")
                else None
            ),
            "intrusion_detection_private_ranges": (
                json.dumps(intrusion_config.get("private_ranges"))
                if intrusion_config.get("private_ranges")
                else None
            ),
            # Rule Collection Groups - security critical (references to actual rules)
            "rule_collection_groups": (
                json.dumps(policy.get("rule_collection_groups"))
                if policy.get("rule_collection_groups")
                else None
            ),
            # Detailed rule groups with actual security rules (ports, protocols, addresses)
            "rule_groups_detail": (
                json.dumps(policy.get("_rule_groups_detail"))
                if policy.get("_rule_groups_detail")
                else None
            ),
            # Parent/Child relationships
            "child_policies": (
                json.dumps(policy.get("child_policies"))
                if policy.get("child_policies")
                else None
            ),
            "firewalls": (
                json.dumps(policy.get("firewalls")) if policy.get("firewalls") else None
            ),
        }

        result.append(transformed)

    return result


def transform_ip_configurations(
    firewalls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform Azure Firewall IP Configurations for ingestion
    Extracts IP configurations from firewalls and creates separate records
    """
    result = []
    for fw in firewalls:
        firewall_id = fw["id"]
        ip_configs = fw.get("ip_configurations", [])

        for ip_config in ip_configs:
            transformed = {
                # Required fields
                "id": ip_config["id"],
                "name": ip_config.get("name"),
                # IP addressing
                "private_ip_address": ip_config.get("private_ip_address"),
                "private_ip_allocation_method": ip_config.get(
                    "private_ip_allocation_method"
                ),
                # Standard fields
                "provisioning_state": ip_config.get("provisioning_state"),
                "type": ip_config.get("type"),
                "etag": ip_config.get("etag"),
                # Relationship fields
                "subnet_id": ip_config.get("subnet", {}).get("id"),
                "public_ip_address_id": ip_config.get("public_ip_address", {}).get(
                    "id"
                ),
                "firewall_id": firewall_id,
            }
            result.append(transformed)

        # Also handle management IP configuration if present
        mgmt_ip_config = fw.get("management_ip_configuration")
        if mgmt_ip_config:
            transformed = {
                "id": mgmt_ip_config["id"],
                "name": mgmt_ip_config.get("name"),
                "private_ip_address": mgmt_ip_config.get("private_ip_address"),
                "private_ip_allocation_method": mgmt_ip_config.get(
                    "private_ip_allocation_method"
                ),
                "provisioning_state": mgmt_ip_config.get("provisioning_state"),
                "type": mgmt_ip_config.get("type"),
                "etag": mgmt_ip_config.get("etag"),
                "subnet_id": mgmt_ip_config.get("subnet", {}).get("id"),
                "public_ip_address_id": mgmt_ip_config.get("public_ip_address", {}).get(
                    "id"
                ),
                "firewall_id": firewall_id,
            }
            result.append(transformed)

    return result


@timeit
def load_firewalls(
    neo4j_session: neo4j.Session,
    firewalls: list[dict[str, Any]],
    azure_subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load Azure Firewalls into Neo4j
    """
    load(
        neo4j_session,
        AzureFirewallSchema(),
        firewalls,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=azure_subscription_id,
    )


@timeit
def load_firewall_policies(
    neo4j_session: neo4j.Session,
    policies: list[dict[str, Any]],
    azure_subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load Azure Firewall Policies into Neo4j
    """
    load(
        neo4j_session,
        AzureFirewallPolicySchema(),
        policies,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=azure_subscription_id,
    )


@timeit
def load_ip_configurations(
    neo4j_session: neo4j.Session,
    ip_configurations: list[dict[str, Any]],
    azure_subscription_id: str,
    update_tag: int,
) -> None:
    """
    Load Azure Firewall IP Configurations into Neo4j
    """
    load(
        neo4j_session,
        AzureFirewallIPConfigurationSchema(),
        ip_configurations,
        lastupdated=update_tag,
        AZURE_SUBSCRIPTION_ID=azure_subscription_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Remove stale Azure Firewall, IP Configuration, and Firewall Policy data
    """
    logger.debug("Running Azure Firewall cleanup job")
    GraphJob.from_node_schema(AzureFirewallSchema(), common_job_parameters).run(
        neo4j_session
    )

    logger.debug("Running Azure Firewall IP Configuration cleanup job")
    GraphJob.from_node_schema(
        AzureFirewallIPConfigurationSchema(), common_job_parameters
    ).run(neo4j_session)

    logger.debug("Running Azure Firewall Policy cleanup job")
    GraphJob.from_node_schema(AzureFirewallPolicySchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    credentials: Credentials,
    subscription_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Azure Firewalls and Firewall Policies to Neo4j

    Follows the standard pattern:
    1. GET - Fetch data from Azure API
    2. TRANSFORM - Shape data for ingestion
    3. LOAD - Ingest to Neo4j using data model
    4. CLEANUP - Remove stale data
    """
    logger.info("Syncing Azure Firewalls and Firewall Policies")

    # Create client
    client = get_client(credentials, subscription_id)

    # GET - Fetch data
    firewalls_data = [_normalize_firewall(fw) for fw in get_firewalls(client)]
    policies_data = [
        _normalize_firewall_policy(policy) for policy in get_firewall_policies(client)
    ]
    ip_groups_data = _to_flattened_snake_case(get_ip_groups(client))

    # Create IP group lookup for enrichment
    ip_group_lookup = {ipg["id"]: ipg for ipg in ip_groups_data}

    # Enrich policies with actual rule data (contains security rules with ports, protocols, etc.)
    for policy in policies_data:
        policy_id = policy.get("id")
        if policy_id:
            rule_groups = _to_flattened_snake_case(
                get_firewall_policy_rule_groups(client, policy_id)
            )
            policy["_rule_groups_detail"] = (
                rule_groups  # Add detailed rules to policy data
            )

    # Enrich firewalls with IP group details (actual IP addresses in rules)
    for firewall in firewalls_data:
        ip_groups = firewall.get("ip_groups", [])
        if ip_groups:
            enriched_groups = []
            for ipg_ref in ip_groups:
                ipg_id = ipg_ref.get("id") if isinstance(ipg_ref, dict) else ipg_ref
                if ipg_id and ipg_id in ip_group_lookup:
                    enriched_groups.append(ip_group_lookup[ipg_id])
            if enriched_groups:
                firewall["_ip_groups_detail"] = enriched_groups

    # TRANSFORM - Shape data
    transformed_firewalls = transform_firewalls(firewalls_data)
    transformed_policies = transform_firewall_policies(policies_data)
    transformed_ip_configurations = transform_ip_configurations(firewalls_data)

    # LOAD - Ingest to Neo4j
    # Load policies first (they're referenced by firewalls)
    load_firewall_policies(
        neo4j_session, transformed_policies, subscription_id, update_tag
    )
    # Load firewalls next (they're referenced by IP configurations)
    load_firewalls(neo4j_session, transformed_firewalls, subscription_id, update_tag)
    # Load IP configurations last (they reference firewalls, subnets, and public IPs)
    load_ip_configurations(
        neo4j_session, transformed_ip_configurations, subscription_id, update_tag
    )

    # CLEANUP - Remove stale data
    cleanup(neo4j_session, common_job_parameters)
