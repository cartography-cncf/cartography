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
class GCPCryptoKeyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    rotation_period: PropertyRef = PropertyRef("rotation_period")
    purpose: PropertyRef = PropertyRef("purpose")
    state: PropertyRef = PropertyRef("state")
    key_ring_id: PropertyRef = PropertyRef("key_ring_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCryptoKeyToGCPKeyRingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCryptoKeyToGCPKeyRingRel(CartographyRelSchema):
    target_node_label: str = "GCPKeyRing"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("key_ring_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPCryptoKeyToGCPKeyRingRelProperties = (
        GCPCryptoKeyToGCPKeyRingRelProperties()
    )


@dataclass(frozen=True)
class GCPCryptoKeyToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPCryptoKeyToGCPProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPCryptoKeyToGCPProjectRelProperties = (
        GCPCryptoKeyToGCPProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPCryptoKeySchema(CartographyNodeSchema):
    label: str = "GCPCryptoKey"
    properties: GCPCryptoKeyProperties = GCPCryptoKeyProperties()
    sub_resource_relationship: GCPCryptoKeyToGCPProjectRel = (
        GCPCryptoKeyToGCPProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPCryptoKeyToGCPKeyRingRel(),
        ],
    )
