from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
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
    provisioning_state: PropertyRef = PropertyRef("provisioningState")
    threat_intel_mode: PropertyRef = PropertyRef("threatIntelMode")
    size: PropertyRef = PropertyRef("size")
    sku_tier: PropertyRef = PropertyRef("sku_tier")
    base_policy_id: PropertyRef = PropertyRef("basePolicyId")
    
    # DNS Settings
    dns_enable_proxy: PropertyRef = PropertyRef("dnsEnableProxy")
    dns_require_proxy_for_network_rules: PropertyRef = PropertyRef("dnsRequireProxyForNetworkRules")
    dns_servers: PropertyRef = PropertyRef("dnsServers")
    
    # SQL Settings
    sql_allow_sql_redirect: PropertyRef = PropertyRef("sqlAllowSqlRedirect")
    
    # SNAT Settings
    snat_private_ranges: PropertyRef = PropertyRef("snatPrivateRanges")
    snat_auto_learn_private_ranges: PropertyRef = PropertyRef("snatAutoLearnPrivateRanges")
    
    # Explicit Proxy Settings
    explicit_proxy_enable: PropertyRef = PropertyRef("explicitProxyEnable")
    explicit_proxy_http_port: PropertyRef = PropertyRef("explicitProxyHttpPort")
    explicit_proxy_https_port: PropertyRef = PropertyRef("explicitProxyHttpsPort")
    explicit_proxy_enable_pac_file: PropertyRef = PropertyRef("explicitProxyEnablePacFile")
    explicit_proxy_pac_file_port: PropertyRef = PropertyRef("explicitProxyPacFilePort")
    explicit_proxy_pac_file: PropertyRef = PropertyRef("explicitProxyPacFile")
    
    # Intrusion Detection Settings
    intrusion_detection_mode: PropertyRef = PropertyRef("intrusionDetectionMode")
    intrusion_detection_profile: PropertyRef = PropertyRef("intrusionDetectionProfile")
    
    # Insights Settings
    insights_is_enabled: PropertyRef = PropertyRef("insightsIsEnabled")
    insights_retention_days: PropertyRef = PropertyRef("insightsRetentionDays")
    
    # Transport Security
    transport_security_ca_name: PropertyRef = PropertyRef("transportSecurityCaName")
    transport_security_key_vault_secret_id: PropertyRef = PropertyRef("transportSecurityKeyVaultSecretId")
    
    # Threat Intel Whitelist - IPs and FQDNs that bypass threat intelligence
    threat_intel_whitelist_ip_addresses: PropertyRef = PropertyRef("threatIntelWhitelistIpAddresses")
    threat_intel_whitelist_fqdns: PropertyRef = PropertyRef("threatIntelWhitelistFqdns")
    
    # Intrusion Detection - detailed security rules
    intrusion_detection_signature_overrides: PropertyRef = PropertyRef("intrusionDetectionSignatureOverrides")
    intrusion_detection_bypass_traffic: PropertyRef = PropertyRef("intrusionDetectionBypassTraffic")
    intrusion_detection_private_ranges: PropertyRef = PropertyRef("intrusionDetectionPrivateRanges")
    
    # Rule Collection Groups - references to actual firewall rule sets
    rule_collection_groups: PropertyRef = PropertyRef("ruleCollectionGroups")
    
    # Detailed rule groups with full security rule data (ports, protocols, addresses)
    rule_groups_detail: PropertyRef = PropertyRef("ruleGroupsDetail")
    
    # Parent/Child Policy relationships
    child_policies: PropertyRef = PropertyRef("childPolicies")
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
    Defines the relationship from an Azure Firewall Policy to an Azure Subscription.
    (:AzureFirewallPolicy)-[:RESOURCE]->(:AzureSubscription)
    """
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: AzureFirewallPolicyToSubscriptionRelProperties = AzureFirewallPolicyToSubscriptionRelProperties()


@dataclass(frozen=True)
class AzureFirewallPolicySchema(CartographyNodeSchema):
    """
    Schema for Azure Firewall Policy nodes in the graph
    """
    label: str = "AzureFirewallPolicy"
    properties: AzureFirewallPolicyProperties = AzureFirewallPolicyProperties()
    sub_resource_relationship: AzureFirewallPolicyToSubscriptionRel = AzureFirewallPolicyToSubscriptionRel()
