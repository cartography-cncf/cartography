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
from cartography.models.extra_labels import IP_PERMISSION_EGRESS
from cartography.models.extra_labels import IP_PERMISSION_INBOUND
from cartography.models.extra_labels import IP_RULE


@dataclass(frozen=True)
class TencentCloudSecurityGroupRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "`<security group ID>/<direction>/<policy index>`. Tencent Cloud assigns rules no "
            "stable ID; the index is the rule's evaluation position."
        ),
    )
    security_group_id: PropertyRef = PropertyRef(
        "security_group_id",
        extra_index=True,
        description="ID of the security group that contains the rule.",
    )
    direction: PropertyRef = PropertyRef(
        "direction", description="`ingress` or `egress`."
    )
    policy_index: PropertyRef = PropertyRef(
        "policy_index",
        description="Position of the rule in its direction's list. Rules are evaluated in this order.",
    )
    action: PropertyRef = PropertyRef("action", description="`ACCEPT` or `DROP`.")
    protocol: PropertyRef = PropertyRef(
        "protocol", description="`TCP`, `UDP`, `ICMP`, `ICMPv6`, or `ALL`."
    )
    port: PropertyRef = PropertyRef(
        "port",
        description="Raw port expression: `all`, a single port, a `low-high` range, or a comma-separated list.",
    )
    fromport: PropertyRef = PropertyRef(
        "fromport",
        description="Lowest port the rule matches. Unset when `port` is a comma-separated list.",
    )
    toport: PropertyRef = PropertyRef(
        "toport",
        description="Highest port the rule matches. Unset when `port` is a comma-separated list.",
    )
    cidr_block: PropertyRef = PropertyRef(
        "cidr_block", description="IPv4 CIDR or address the rule matches."
    )
    ipv6_cidr_block: PropertyRef = PropertyRef(
        "ipv6_cidr_block", description="IPv6 CIDR or address the rule matches."
    )
    source_security_group_id: PropertyRef = PropertyRef(
        "source_security_group_id",
        description="Security group whose members the rule matches, instead of a CIDR.",
    )
    address_template_id: PropertyRef = PropertyRef(
        "address_template_id",
        description="IP address template or template group the rule matches, instead of a CIDR.",
    )
    service_template_id: PropertyRef = PropertyRef(
        "service_template_id",
        description="Protocol/port template or template group the rule matches, instead of `protocol` and `port`.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the rule."
    )
    modify_time: PropertyRef = PropertyRef(
        "modify_time", description="Time the rule was last modified."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudSecurityGroupRuleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudSecurityGroupRule)
class TencentCloudSecurityGroupRuleToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its security group rules."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudSecurityGroupRuleToAccountRelProperties = (
        TencentCloudSecurityGroupRuleToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudSecurityGroupRuleToSecurityGroupRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudSecurityGroupRule)-[:MEMBER_OF_SECURITY_GROUP]->(:TencentCloudSecurityGroup)
class TencentCloudSecurityGroupRuleToSecurityGroupRel(CartographyRelSchema):
    """Connects a rule to the security group that contains it."""

    target_node_label: str = "TencentCloudSecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("security_group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_SECURITY_GROUP"
    properties: TencentCloudSecurityGroupRuleToSecurityGroupRelProperties = (
        TencentCloudSecurityGroupRuleToSecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudSecurityGroupRuleSchema(CartographyNodeSchema):
    """One ingress or egress rule of a security group. Rules with action `ACCEPT` also
    carry the shared `IpPermissionInbound` / `IpPermissionEgress` labels."""

    label: str = "TencentCloudSecurityGroupRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            IP_PERMISSION_INBOUND.when(direction="ingress", action="ACCEPT"),
            IP_PERMISSION_EGRESS.when(direction="egress", action="ACCEPT"),
            IP_RULE,
        ],
    )
    properties: TencentCloudSecurityGroupRuleNodeProperties = (
        TencentCloudSecurityGroupRuleNodeProperties()
    )
    sub_resource_relationship: TencentCloudSecurityGroupRuleToAccountRel = (
        TencentCloudSecurityGroupRuleToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [TencentCloudSecurityGroupRuleToSecurityGroupRel()],
    )
