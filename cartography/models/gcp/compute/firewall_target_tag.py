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
class GCPFirewallTargetTagNodeProperties(CartographyNodeProperties):
    """Properties for GCPNetworkTag nodes created as firewall target tags."""

    id: PropertyRef = PropertyRef("tag_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    tag_id: PropertyRef = PropertyRef("tag_id", extra_index=True)
    value: PropertyRef = PropertyRef("value")


@dataclass(frozen=True)
class GCPFirewallTargetTagToFirewallRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPFirewallTargetTagToFirewallRel(CartographyRelSchema):
    target_node_label: str = "GCPFirewall"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("fw_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TARGET_TAG"
    properties: GCPFirewallTargetTagToFirewallRelProperties = (
        GCPFirewallTargetTagToFirewallRelProperties()
    )


@dataclass(frozen=True)
class GCPFirewallTargetTagToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPFirewallTargetTagToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("vpc_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEFINED_IN"
    properties: GCPFirewallTargetTagToVpcRelProperties = (
        GCPFirewallTargetTagToVpcRelProperties()
    )


@dataclass(frozen=True)
class GCPFirewallTargetTagToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPFirewallTargetTagToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPFirewallTargetTagToProjectRelProperties = (
        GCPFirewallTargetTagToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPFirewallTargetTagSchema(CartographyNodeSchema):
    """
    Schema for GCPNetworkTag nodes that are target tags of firewalls.
    This creates the TARGET_TAG relationship from GCPFirewall to GCPNetworkTag.
    """

    label: str = "GCPNetworkTag"
    properties: GCPFirewallTargetTagNodeProperties = (
        GCPFirewallTargetTagNodeProperties()
    )
    sub_resource_relationship: GCPFirewallTargetTagToProjectRel = (
        GCPFirewallTargetTagToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPFirewallTargetTagToFirewallRel(),
            GCPFirewallTargetTagToVpcRel(),
        ]
    )
