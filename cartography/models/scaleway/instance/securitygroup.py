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


@dataclass(frozen=True)
class ScalewaySecurityGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    enable_default_security: PropertyRef = PropertyRef("enable_default_security")
    inbound_default_policy: PropertyRef = PropertyRef("inbound_default_policy")
    outbound_default_policy: PropertyRef = PropertyRef("outbound_default_policy")
    stateful: PropertyRef = PropertyRef("stateful")
    project_default: PropertyRef = PropertyRef("project_default")
    organization_default: PropertyRef = PropertyRef("organization_default")
    tags: PropertyRef = PropertyRef("tags")
    state: PropertyRef = PropertyRef("state")
    zone: PropertyRef = PropertyRef("zone")
    creation_date: PropertyRef = PropertyRef("creation_date")
    modification_date: PropertyRef = PropertyRef("modification_date")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewaySecurityGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecurityGroup)
class ScalewaySecurityGroupToProjectRel(CartographyRelSchema):
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
    id: PropertyRef = PropertyRef("id")
    protocol: PropertyRef = PropertyRef("protocol")
    direction: PropertyRef = PropertyRef("direction")
    action: PropertyRef = PropertyRef("action")
    ip_range: PropertyRef = PropertyRef("ip_range")
    dest_port_from: PropertyRef = PropertyRef("dest_port_from")
    dest_port_to: PropertyRef = PropertyRef("dest_port_to")
    position: PropertyRef = PropertyRef("position")
    editable: PropertyRef = PropertyRef("editable")
    zone: PropertyRef = PropertyRef("zone")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewaySecurityGroupRuleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecurityGroupRule)
class ScalewaySecurityGroupRuleToProjectRel(CartographyRelSchema):
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
    """Schema for inbound rules. Carries the cross-cloud `IpRule` and
    `IpPermissionInbound` semantic labels so it is matched alongside the
    AWS / GCP / Azure equivalents."""

    label: str = "ScalewaySecurityGroupRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["IpPermissionInbound", "IpRule"]
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
    """Schema for outbound rules. Carries the cross-cloud `IpRule` and
    `IpPermissionEgress` semantic labels."""

    label: str = "ScalewaySecurityGroupRule"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["IpPermissionEgress", "IpRule"]
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
