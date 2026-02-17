from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureFirewallPolicyProperties(CartographyNodeProperties):
    """
    Properties for Azure Firewall Policy nodes
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    type: PropertyRef = PropertyRef("type")
    etag: PropertyRef = PropertyRef("etag")
    tags: PropertyRef = PropertyRef("tags")
    provisioning_state: PropertyRef = PropertyRef("provisioning_state")
    threat_intel_mode: PropertyRef = PropertyRef("threat_intel_mode")
    size: PropertyRef = PropertyRef("size")
    sku_tier: PropertyRef = PropertyRef("sku_tier")
    base_policy_id: PropertyRef = PropertyRef("base_policy_id")

    # DNS Settings
    dns_enable_proxy: PropertyRef = PropertyRef("dns_enable_proxy")
    dns_require_proxy_for_network_rules: PropertyRef = PropertyRef(
        "dns_require_proxy_for_network_rules",
    )
    dns_servers: PropertyRef = PropertyRef("dns_servers")

    # SQL Settings
    sql_allow_sql_redirect: PropertyRef = PropertyRef("sql_allow_sql_redirect")

    # SNAT Settings
    snat_private_ranges: PropertyRef = PropertyRef("snat_private_ranges")
    snat_auto_learn_private_ranges: PropertyRef = PropertyRef(
        "snat_auto_learn_private_ranges",
    )

    # Explicit Proxy Settings
    explicit_proxy_enable: PropertyRef = PropertyRef("explicit_proxy_enable")
    explicit_proxy_http_port: PropertyRef = PropertyRef("explicit_proxy_http_port")
    explicit_proxy_https_port: PropertyRef = PropertyRef("explicit_proxy_https_port")
    explicit_proxy_enable_pac_file: PropertyRef = PropertyRef(
        "explicit_proxy_enable_pac_file",
    )
    explicit_proxy_pac_file_port: PropertyRef = PropertyRef(
        "explicit_proxy_pac_file_port"
    )
    explicit_proxy_pac_file: PropertyRef = PropertyRef("explicit_proxy_pac_file")

    # Intrusion Detection Settings
    intrusion_detection_mode: PropertyRef = PropertyRef("intrusion_detection_mode")
    intrusion_detection_profile: PropertyRef = PropertyRef(
        "intrusion_detection_profile"
    )

    # Insights Settings
    insights_is_enabled: PropertyRef = PropertyRef("insights_is_enabled")
    insights_retention_days: PropertyRef = PropertyRef("insights_retention_days")

    # Transport Security
    transport_security_ca_name: PropertyRef = PropertyRef("transport_security_ca_name")
    transport_security_key_vault_secret_id: PropertyRef = PropertyRef(
        "transport_security_key_vault_secret_id",
    )

    # Threat Intel Whitelist - IPs and FQDNs that bypass threat intelligence
    threat_intel_whitelist_ip_addresses: PropertyRef = PropertyRef(
        "threat_intel_whitelist_ip_addresses",
    )
    threat_intel_whitelist_fqdns: PropertyRef = PropertyRef(
        "threat_intel_whitelist_fqdns"
    )

    # Intrusion Detection - detailed security rules
    intrusion_detection_signature_overrides: PropertyRef = PropertyRef(
        "intrusion_detection_signature_overrides",
    )
    intrusion_detection_bypass_traffic: PropertyRef = PropertyRef(
        "intrusion_detection_bypass_traffic",
    )
    intrusion_detection_private_ranges: PropertyRef = PropertyRef(
        "intrusion_detection_private_ranges",
    )

    # Rule Collection Groups - references to actual firewall rule sets
    rule_collection_groups: PropertyRef = PropertyRef("rule_collection_groups")

    # Detailed rule groups with full security rule data (ports, protocols, addresses)
    rule_groups_detail: PropertyRef = PropertyRef("rule_groups_detail")

    # Parent/Child Policy relationships
    child_policies: PropertyRef = PropertyRef("child_policies")
    firewalls: PropertyRef = PropertyRef("firewalls")


@dataclass(frozen=True)
class AzureFirewallPolicyToSubscriptionRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between Azure Firewall Policy and Azure Subscription
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallPolicyToSubscriptionRel(CartographyRelSchema):
    """
    Defines the relationship from an Azure Subscription to an Azure Firewall Policy.
    (:AzureSubscription)-[:RESOURCE]->(:AzureFirewallPolicy)
    """

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureFirewallPolicyToSubscriptionRelProperties = (
        AzureFirewallPolicyToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallPolicyToParentPolicyRelProperties(CartographyRelProperties):
    """
    Properties for the INHERITS_FROM relationship between child and parent policies
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallPolicyToParentPolicyRel(CartographyRelSchema):
    """
    Defines the relationship from a child policy to its parent policy.
    (:AzureFirewallPolicy)-[:INHERITS_FROM]->(:AzureFirewallPolicy)

    Azure Firewall Policies support inheritance, where a child policy can inherit
    settings from a parent (base) policy. This allows centralized management of
    common firewall rules and settings across multiple policies.
    """

    target_node_label: str = "AzureFirewallPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("base_policy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INHERITS_FROM"
    properties: AzureFirewallPolicyToParentPolicyRelProperties = (
        AzureFirewallPolicyToParentPolicyRelProperties()
    )


@dataclass(frozen=True)
class AzureFirewallPolicySchema(CartographyNodeSchema):
    """
    Schema for Azure Firewall Policy nodes in the graph
    """

    label: str = "AzureFirewallPolicy"
    properties: AzureFirewallPolicyProperties = AzureFirewallPolicyProperties()
    sub_resource_relationship: AzureFirewallPolicyToSubscriptionRel = (
        AzureFirewallPolicyToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureFirewallPolicyToParentPolicyRel(),
        ]
    )
