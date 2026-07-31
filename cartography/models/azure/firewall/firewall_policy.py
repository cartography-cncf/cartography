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

    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the firewall policy."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Name of the firewall policy.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region containing the firewall policy."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Azure resource type of the firewall policy."
    )
    etag: PropertyRef = PropertyRef(
        "etag",
        description="Entity tag that changes when the firewall policy is updated.",
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Azure resource tags assigned to the firewall policy."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the firewall policy.",
    )
    threat_intel_mode: PropertyRef = PropertyRef(
        "threat_intel_mode",
        description="Operating mode for threat intelligence filtering.",
    )
    size: PropertyRef = PropertyRef(
        "size", description="Current size of the firewall policy."
    )
    sku_tier: PropertyRef = PropertyRef(
        "sku_tier", description="Tier of the firewall policy SKU."
    )
    base_policy_id: PropertyRef = PropertyRef(
        "base_policy_id", description="Azure resource ID of the parent firewall policy."
    )

    # DNS Settings
    dns_enable_proxy: PropertyRef = PropertyRef(
        "dns_enable_proxy", description="Whether DNS proxy is enabled."
    )
    dns_require_proxy_for_network_rules: PropertyRef = PropertyRef(
        "dns_require_proxy_for_network_rules",
        description="Whether network rules require DNS proxy.",
    )
    dns_servers: PropertyRef = PropertyRef(
        "dns_servers", description="Custom DNS servers used by the firewall policy."
    )

    # SQL Settings
    sql_allow_sql_redirect: PropertyRef = PropertyRef(
        "sql_allow_sql_redirect", description="Whether SQL redirect traffic is allowed."
    )

    # SNAT Settings
    snat_private_ranges: PropertyRef = PropertyRef(
        "snat_private_ranges",
        description="Private IP ranges that are not source NAT translated.",
    )
    snat_auto_learn_private_ranges: PropertyRef = PropertyRef(
        "snat_auto_learn_private_ranges",
        description="Mode for automatically learning private ranges excluded from source NAT.",
    )

    # Explicit Proxy Settings
    explicit_proxy_enable: PropertyRef = PropertyRef(
        "explicit_proxy_enable", description="Whether explicit proxy is enabled."
    )
    explicit_proxy_http_port: PropertyRef = PropertyRef(
        "explicit_proxy_http_port", description="Port used by the explicit HTTP proxy."
    )
    explicit_proxy_https_port: PropertyRef = PropertyRef(
        "explicit_proxy_https_port",
        description="Port used by the explicit HTTPS proxy.",
    )
    explicit_proxy_enable_pac_file: PropertyRef = PropertyRef(
        "explicit_proxy_enable_pac_file",
        description="Whether a proxy auto-configuration file is enabled.",
    )
    explicit_proxy_pac_file_port: PropertyRef = PropertyRef(
        "explicit_proxy_pac_file_port",
        description="Port used to serve the proxy auto-configuration file.",
    )
    explicit_proxy_pac_file: PropertyRef = PropertyRef(
        "explicit_proxy_pac_file",
        description="URL of the proxy auto-configuration file.",
    )

    # Intrusion Detection Settings
    intrusion_detection_mode: PropertyRef = PropertyRef(
        "intrusion_detection_mode",
        description="Operating mode for intrusion detection.",
    )
    intrusion_detection_profile: PropertyRef = PropertyRef(
        "intrusion_detection_profile",
        description="Intrusion detection profile used by the policy.",
    )

    # Insights Settings
    insights_is_enabled: PropertyRef = PropertyRef(
        "insights_is_enabled",
        description="Whether firewall policy insights are enabled.",
    )
    insights_retention_days: PropertyRef = PropertyRef(
        "insights_retention_days",
        description="Number of days firewall policy insights are retained.",
    )

    # Transport Security
    transport_security_ca_name: PropertyRef = PropertyRef(
        "transport_security_ca_name",
        description="Name of the certificate authority used for TLS inspection.",
    )
    transport_security_key_vault_secret_id: PropertyRef = PropertyRef(
        "transport_security_key_vault_secret_id",
        description="Key Vault secret ID of the TLS inspection certificate.",
    )

    # Threat Intel Whitelist - IPs and FQDNs that bypass threat intelligence
    threat_intel_whitelist_ip_addresses: PropertyRef = PropertyRef(
        "threat_intel_whitelist_ip_addresses",
        description="IP addresses excluded from threat intelligence filtering.",
    )
    threat_intel_whitelist_fqdns: PropertyRef = PropertyRef(
        "threat_intel_whitelist_fqdns",
        description="Fully qualified domain names excluded from threat intelligence filtering.",
    )

    # Intrusion Detection - detailed security rules
    intrusion_detection_signature_overrides: PropertyRef = PropertyRef(
        "intrusion_detection_signature_overrides",
        description="Intrusion detection signature mode overrides.",
    )
    intrusion_detection_bypass_traffic: PropertyRef = PropertyRef(
        "intrusion_detection_bypass_traffic",
        description="Traffic bypass settings for intrusion detection.",
    )
    intrusion_detection_private_ranges: PropertyRef = PropertyRef(
        "intrusion_detection_private_ranges",
        description="Private IP ranges used by intrusion detection.",
    )

    # Rule Collection Groups - references to actual firewall rule sets
    rule_collection_groups: PropertyRef = PropertyRef(
        "rule_collection_groups",
        description="Rule collection groups referenced by the firewall policy.",
    )

    # Detailed rule groups with full security rule data (ports, protocols, addresses)
    rule_groups_detail: PropertyRef = PropertyRef(
        "rule_groups_detail",
        description="Rule collection groups and their firewall rules.",
    )

    # Parent/Child Policy relationships
    child_policies: PropertyRef = PropertyRef(
        "child_policies", description="Firewall policies that inherit from this policy."
    )
    firewalls: PropertyRef = PropertyRef(
        "firewalls", description="Firewalls associated with this policy."
    )


@dataclass(frozen=True)
class AzureFirewallPolicyToSubscriptionRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between Azure Firewall Policy and Azure Subscription
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFirewallPolicyToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the firewall policy as a resource."""

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
    """An Azure Firewall Policy inherits settings from a parent policy."""

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
    """An Azure Firewall Policy that defines firewall security and operational settings."""

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
