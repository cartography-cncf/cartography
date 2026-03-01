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
class TailscaleDevicePostureAttributeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key")
    value: PropertyRef = PropertyRef("value")
    updated: PropertyRef = PropertyRef("updated")


@dataclass(frozen=True)
class TailscaleDevicePostureAttributeToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleDevicePostureAttribute)
class TailscaleDevicePostureAttributeToTailnetRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TailscaleDevicePostureAttributeToTailnetRelProperties = (
        TailscaleDevicePostureAttributeToTailnetRelProperties()
    )


@dataclass(frozen=True)
class TailscaleDevicePostureAttributeToDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleDevice)-[:HAS_POSTURE_ATTRIBUTE]->(:TailscaleDevicePostureAttribute)
class TailscaleDevicePostureAttributeToDeviceRel(CartographyRelSchema):
    target_node_label: str = "TailscaleDevice"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_POSTURE_ATTRIBUTE"
    properties: TailscaleDevicePostureAttributeToDeviceRelProperties = (
        TailscaleDevicePostureAttributeToDeviceRelProperties()
    )


@dataclass(frozen=True)
class TailscaleDevicePostureAttributeSchema(CartographyNodeSchema):
    label: str = "TailscaleDevicePostureAttribute"
    properties: TailscaleDevicePostureAttributeNodeProperties = (
        TailscaleDevicePostureAttributeNodeProperties()
    )
    sub_resource_relationship: TailscaleDevicePostureAttributeToTailnetRel = (
        TailscaleDevicePostureAttributeToTailnetRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TailscaleDevicePostureAttributeToDeviceRel(),
        ]
    )
