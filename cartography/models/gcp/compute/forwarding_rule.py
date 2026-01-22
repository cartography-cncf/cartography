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
class GCPForwardingRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("partial_uri")
    partial_uri: PropertyRef = PropertyRef("partial_uri")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ip_address: PropertyRef = PropertyRef("ip_address")
    ip_protocol: PropertyRef = PropertyRef("ip_protocol")
    load_balancing_scheme: PropertyRef = PropertyRef("load_balancing_scheme")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    network: PropertyRef = PropertyRef("network_partial_uri")
    port_range: PropertyRef = PropertyRef("port_range")
    ports: PropertyRef = PropertyRef("ports")
    project_id: PropertyRef = PropertyRef("project_id")
    region: PropertyRef = PropertyRef("region")
    self_link: PropertyRef = PropertyRef("self_link")
    subnetwork: PropertyRef = PropertyRef("subnetwork_partial_uri")
    target: PropertyRef = PropertyRef("target")


@dataclass(frozen=True)
class GCPForwardingRuleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPForwardingRuleToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPForwardingRuleToProjectRelProperties = (
        GCPForwardingRuleToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPForwardingRuleToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPForwardingRuleToSubnetRel(CartographyRelSchema):
    target_node_label: str = "GCPSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("subnetwork_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPForwardingRuleToSubnetRelProperties = (
        GCPForwardingRuleToSubnetRelProperties()
    )


@dataclass(frozen=True)
class GCPForwardingRuleToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPForwardingRuleToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("network_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPForwardingRuleToVpcRelProperties = (
        GCPForwardingRuleToVpcRelProperties()
    )


@dataclass(frozen=True)
class GCPForwardingRuleSchema(CartographyNodeSchema):
    """
    Schema for GCP Forwarding Rules.
    Note: The relationships to subnet and VPC are handled separately in intel code
    because only one of them should be created based on whether the rule has a subnetwork or network.
    """

    label: str = "GCPForwardingRule"
    properties: GCPForwardingRuleNodeProperties = GCPForwardingRuleNodeProperties()
    sub_resource_relationship: GCPForwardingRuleToProjectRel = (
        GCPForwardingRuleToProjectRel()
    )


@dataclass(frozen=True)
class GCPForwardingRuleWithSubnetSchema(CartographyNodeSchema):
    """
    Schema for GCP Forwarding Rules that have a subnetwork (INTERNAL load balancing).
    """

    label: str = "GCPForwardingRule"
    properties: GCPForwardingRuleNodeProperties = GCPForwardingRuleNodeProperties()
    sub_resource_relationship: GCPForwardingRuleToProjectRel = (
        GCPForwardingRuleToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPForwardingRuleToSubnetRel(),
        ]
    )


@dataclass(frozen=True)
class GCPForwardingRuleWithVpcSchema(CartographyNodeSchema):
    label: str = "GCPForwardingRule"
    properties: GCPForwardingRuleNodeProperties = GCPForwardingRuleNodeProperties()
    sub_resource_relationship: GCPForwardingRuleToProjectRel = (
        GCPForwardingRuleToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPForwardingRuleToVpcRel(),
        ]
    )
