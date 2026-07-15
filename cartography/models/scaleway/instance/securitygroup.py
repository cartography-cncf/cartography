from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewaySecurityGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Security Group unique ID.")
    name: PropertyRef = PropertyRef("name", description="Security Group name.")
    description: PropertyRef = PropertyRef(
        "description", description="Security Group description."
    )
    enable_default_security: PropertyRef = PropertyRef(
        "enable_default_security",
        description="True if SMTP is blocked on IPv4 and IPv6.",
    )
    inbound_default_policy: PropertyRef = PropertyRef(
        "inbound_default_policy",
        description="Default inbound policy (`accept`, `drop`).",
    )
    outbound_default_policy: PropertyRef = PropertyRef(
        "outbound_default_policy",
        description="Default outbound policy (`accept`, `drop`).",
    )
    stateful: PropertyRef = PropertyRef(
        "stateful", description="True if the Security Group is stateful."
    )
    project_default: PropertyRef = PropertyRef(
        "project_default",
        description="True if it is the default Security Group for the Project.",
    )
    organization_default: PropertyRef = PropertyRef(
        "organization_default",
        description="True if it is the default Security Group for the Organization.",
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the Security Group."
    )
    state: PropertyRef = PropertyRef("state", description="Security Group state.")
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone in which the Security Group is located."
    )
    creation_date: PropertyRef = PropertyRef(
        "creation_date", description="Security Group creation date."
    )
    modification_date: PropertyRef = PropertyRef(
        "modification_date", description="Security Group modification date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewaySecurityGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecurityGroup)
class ScalewaySecurityGroupToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewaySecurityGroup` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewaySecurityGroupToProjectRelProperties = (
        ScalewaySecurityGroupToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySecurityGroupToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayInstance)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:ScalewaySecurityGroup)
class ScalewaySecurityGroupToInstanceRel(CartographyRelSchema):
    """Connects `ScalewayInstance` to `ScalewaySecurityGroup` through
    `MEMBER_OF_SCALEWAY_SECURITY_GROUP`.
    """

    target_node_label: str = "ScalewayInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("servers_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_SCALEWAY_SECURITY_GROUP"
    properties: ScalewaySecurityGroupToInstanceRelProperties = (
        ScalewaySecurityGroupToInstanceRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySecurityGroupSchema(CartographyNodeSchema):
    """A Security Group is a set of firewall rules that controls inbound and outbound
    traffic for the Instances attached to it.
    """

    label: str = "ScalewaySecurityGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["NetworkAccessControl"])
    properties: ScalewaySecurityGroupProperties = ScalewaySecurityGroupProperties()
    sub_resource_relationship: ScalewaySecurityGroupToProjectRel = (
        ScalewaySecurityGroupToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewaySecurityGroupToInstanceRel(),
        ]
    )


@dataclass(frozen=True)
class ScalewaySecurityGroupRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Rule unique ID.")
    protocol: PropertyRef = PropertyRef(
        "protocol",
        description="Protocol the rule applies to (`tcp`, `udp`, `icmp`, `any`).",
    )
    direction: PropertyRef = PropertyRef(
        "direction", description="Rule direction (`inbound`, `outbound`)."
    )
    action: PropertyRef = PropertyRef(
        "action", description="Action taken on matching traffic (`accept`, `drop`)."
    )
    ip_range: PropertyRef = PropertyRef(
        "ip_range", description="IP range the rule applies to (CIDR notation)."
    )
    dest_port_from: PropertyRef = PropertyRef(
        "dest_port_from", description="Beginning of the destination port range."
    )
    dest_port_to: PropertyRef = PropertyRef(
        "dest_port_to", description="End of the destination port range."
    )
    position: PropertyRef = PropertyRef(
        "position", description="Rule position (evaluation order)."
    )
    editable: PropertyRef = PropertyRef(
        "editable", description="True if the rule is editable."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone in which the rule is located."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewaySecurityGroupRuleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecurityGroupRule)
class ScalewaySecurityGroupRuleToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewaySecurityGroupRule` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewaySecurityGroupRuleToProjectRelProperties = (
        ScalewaySecurityGroupRuleToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySecurityGroupRuleToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewaySecurityGroupRule)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:ScalewaySecurityGroup)
class ScalewaySecurityGroupRuleToGroupRel(CartographyRelSchema):
    """Connects `ScalewaySecurityGroupRule` to `ScalewaySecurityGroup` through
    `MEMBER_OF_SCALEWAY_SECURITY_GROUP`.
    """

    target_node_label: str = "ScalewaySecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("security_group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_SCALEWAY_SECURITY_GROUP"
    properties: ScalewaySecurityGroupRuleToGroupRelProperties = (
        ScalewaySecurityGroupRuleToGroupRelProperties()
    )


@dataclass(frozen=True)
class ScalewayInboundSecurityGroupRuleSchema(CartographyNodeSchema):
    """A Security Group Rule is a single firewall rule (inbound or outbound) belonging to a
    Security Group.
    """

    label: str = "ScalewaySecurityGroupRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "IpRule",
            ConditionalNodeLabel(
                label="IpPermissionInbound",
                conditions={"direction": "inbound"},
            ),
        ]
    )
    properties: ScalewaySecurityGroupRuleProperties = (
        ScalewaySecurityGroupRuleProperties()
    )
    sub_resource_relationship: ScalewaySecurityGroupRuleToProjectRel = (
        ScalewaySecurityGroupRuleToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewaySecurityGroupRuleToGroupRel(),
        ]
    )


@dataclass(frozen=True)
class ScalewayOutboundSecurityGroupRuleSchema(CartographyNodeSchema):
    """A Security Group Rule is a single firewall rule (inbound or outbound) belonging to a
    Security Group.
    """

    label: str = "ScalewaySecurityGroupRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "IpRule",
            ConditionalNodeLabel(
                label="IpPermissionEgress",
                conditions={"direction": "outbound"},
            ),
        ]
    )
    properties: ScalewaySecurityGroupRuleProperties = (
        ScalewaySecurityGroupRuleProperties()
    )
    sub_resource_relationship: ScalewaySecurityGroupRuleToProjectRel = (
        ScalewaySecurityGroupRuleToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewaySecurityGroupRuleToGroupRel(),
        ]
    )
