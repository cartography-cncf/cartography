from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL


@dataclass(frozen=True)
class WAFWebACLNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "ARN",
        description="The ARN of the AWS WAF web ACL.",
    )
    arn: PropertyRef = PropertyRef(
        "ARN",
        extra_index=True,
        description="The ARN of the AWS WAF web ACL.",
    )
    web_acl_id: PropertyRef = PropertyRef(
        "Id",
        description="The AWS-generated identifier of the web ACL.",
    )
    name: PropertyRef = PropertyRef(
        "Name",
        extra_index=True,
        description="The name of the web ACL.",
    )
    description: PropertyRef = PropertyRef(
        "Description",
        description="A description of the web ACL.",
    )
    scope: PropertyRef = PropertyRef(
        "Scope",
        description="Whether the web ACL protects regional or CloudFront resources.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        description="The AWS API region used to retrieve the web ACL.",
    )
    capacity: PropertyRef = PropertyRef(
        "Capacity",
        description="The web ACL capacity units currently used by its rules.",
    )
    default_action: PropertyRef = PropertyRef(
        "DefaultAction",
        description="The action applied when no rule matches.",
    )
    managed_by_firewall_manager: PropertyRef = PropertyRef(
        "ManagedByFirewallManager",
        description="Whether AWS Firewall Manager manages the web ACL.",
    )
    retrofitted_by_firewall_manager: PropertyRef = PropertyRef(
        "RetrofittedByFirewallManager",
        description="Whether AWS Firewall Manager retrofitted the web ACL.",
    )
    label_namespace: PropertyRef = PropertyRef(
        "LabelNamespace",
        description="The namespace AWS WAF uses for labels emitted by this web ACL.",
    )
    token_domains: PropertyRef = PropertyRef(
        "TokenDomains",
        description="Domains accepted for AWS WAF tokens.",
    )
    sampled_requests_enabled: PropertyRef = PropertyRef(
        "SampledRequestsEnabled",
        description="Whether AWS WAF stores sampled requests for the web ACL.",
    )
    cloudwatch_metrics_enabled: PropertyRef = PropertyRef(
        "CloudWatchMetricsEnabled",
        description="Whether CloudWatch metrics are enabled for the web ACL.",
    )
    metric_name: PropertyRef = PropertyRef(
        "MetricName",
        description="The CloudWatch metric name for the web ACL.",
    )
    logging_enabled: PropertyRef = PropertyRef(
        "LoggingEnabled",
        description="Whether request logging is configured for the web ACL.",
    )
    log_destination_arns: PropertyRef = PropertyRef(
        "LogDestinationConfigs",
        description="ARNs of the destinations that receive AWS WAF logs.",
    )
    redacted_field_types: PropertyRef = PropertyRef(
        "RedactedFieldTypes",
        description="Request field types redacted from AWS WAF logs.",
    )
    logging_filter: PropertyRef = PropertyRef(
        "LoggingFilter",
        description="The AWS WAF logging filter encoded as JSON.",
    )
    association_config: PropertyRef = PropertyRef(
        "AssociationConfig",
        description="Per-resource request body inspection settings encoded as JSON.",
    )
    on_source_ddos_protection_config: PropertyRef = PropertyRef(
        "OnSourceDDoSProtectionConfig",
        description="The web ACL's on-source DDoS protection settings encoded as JSON.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WAFWebACLToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WAFWebACLToAWSAccountRel(CartographyRelSchema):
    """Indicates that an AWS account contains the web ACL."""

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WAFWebACLToAWSAccountRelProperties = (
        WAFWebACLToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class WAFWebACLToLoadBalancerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WAFWebACLToLoadBalancerRel(CartographyRelSchema):
    """Indicates that the web ACL protects an Application Load Balancer."""

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("ProtectedLoadBalancerArns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROTECTS"
    properties: WAFWebACLToLoadBalancerRelProperties = (
        WAFWebACLToLoadBalancerRelProperties()
    )


@dataclass(frozen=True)
class WAFWebACLToCognitoUserPoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WAFWebACLToCognitoUserPoolRel(CartographyRelSchema):
    """Indicates that the web ACL protects an Amazon Cognito user pool."""

    target_node_label: str = "AWSCognitoUserPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ProtectedCognitoUserPoolIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROTECTS"
    properties: WAFWebACLToCognitoUserPoolRelProperties = (
        WAFWebACLToCognitoUserPoolRelProperties()
    )


@dataclass(frozen=True)
class WAFWebACLSchema(CartographyNodeSchema):
    """An AWS WAF v2 [web ACL](https://docs.aws.amazon.com/waf/latest/APIReference/API_WebACL.html) that filters HTTP(S) requests for protected resources.

    This node has the extra label `NetworkAccessControl` to enable cross-platform
    queries for network access controls.
    """

    label: str = "AWSWAFWebACL"
    properties: WAFWebACLNodeProperties = WAFWebACLNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([NETWORK_ACCESS_CONTROL])
    sub_resource_relationship: WAFWebACLToAWSAccountRel = WAFWebACLToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            WAFWebACLToLoadBalancerRel(),
            WAFWebACLToCognitoUserPoolRel(),
        ],
    )


@dataclass(frozen=True)
class WAFRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "RuleId",
        description="Stable identifier composed from the owning web ACL and rule.",
    )
    name: PropertyRef = PropertyRef("Name", description="The name of the rule.")
    priority: PropertyRef = PropertyRef(
        "Priority",
        description="The rule evaluation priority within its phase.",
    )
    phase: PropertyRef = PropertyRef(
        "Phase",
        description="The rule phase: regular, Firewall Manager pre-process, or post-process.",
    )
    action: PropertyRef = PropertyRef(
        "Action",
        description="The action applied when the rule matches.",
    )
    override_action: PropertyRef = PropertyRef(
        "OverrideAction",
        description="The action override applied to a referenced rule group.",
    )
    statement_types: PropertyRef = PropertyRef(
        "StatementTypes",
        description="Statement types used by the rule, including nested statements.",
    )
    statement: PropertyRef = PropertyRef(
        "Statement",
        description="The complete AWS WAF statement encoded as JSON.",
    )
    referenced_rule_group_arns: PropertyRef = PropertyRef(
        "ReferencedRuleGroupArns",
        description="ARNs of customer-managed rule groups referenced by the rule.",
    )
    referenced_ip_set_arns: PropertyRef = PropertyRef(
        "ReferencedIPSetArns",
        description="ARNs of IP sets referenced by the rule.",
    )
    referenced_regex_pattern_set_arns: PropertyRef = PropertyRef(
        "ReferencedRegexPatternSetArns",
        description="ARNs of regex pattern sets referenced by the rule.",
    )
    managed_rule_groups: PropertyRef = PropertyRef(
        "ManagedRuleGroups",
        description="Referenced managed rule groups in vendor/name/version form.",
    )
    rate_limits: PropertyRef = PropertyRef(
        "RateLimits",
        description="Request limits from rate-based statements used by the rule.",
    )
    sampled_requests_enabled: PropertyRef = PropertyRef(
        "SampledRequestsEnabled",
        description="Whether AWS WAF stores sampled requests for the rule.",
    )
    cloudwatch_metrics_enabled: PropertyRef = PropertyRef(
        "CloudWatchMetricsEnabled",
        description="Whether CloudWatch metrics are enabled for the rule.",
    )
    metric_name: PropertyRef = PropertyRef(
        "MetricName",
        description="The CloudWatch metric name for the rule.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WAFRuleToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WAFRuleToAWSAccountRel(CartographyRelSchema):
    """Indicates that an AWS account contains the WAF rule."""

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WAFRuleToAWSAccountRelProperties = WAFRuleToAWSAccountRelProperties()


@dataclass(frozen=True)
class WAFRuleToWebACLRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WAFRuleToWebACLRel(CartographyRelSchema):
    """Indicates that a web ACL contains the rule."""

    target_node_label: str = "AWSWAFWebACL"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("WebACLArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULE"
    properties: WAFRuleToWebACLRelProperties = WAFRuleToWebACLRelProperties()


@dataclass(frozen=True)
class WAFRuleSchema(CartographyNodeSchema):
    """A rule evaluated by an AWS WAF web ACL or AWS Firewall Manager phase."""

    label: str = "AWSWAFRule"
    properties: WAFRuleNodeProperties = WAFRuleNodeProperties()
    sub_resource_relationship: WAFRuleToAWSAccountRel = WAFRuleToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([WAFRuleToWebACLRel()])
