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
class TenableAssetSourceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    source_first_seen: PropertyRef = PropertyRef("source_first_seen")
    source_last_seen: PropertyRef = PropertyRef("source_last_seen")


@dataclass(frozen=True)
class TenableAssetSourceToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAssetSource)
@dataclass(frozen=True)
class TenableAssetSourceToTenantRel(CartographyRelSchema):
    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableAssetSourceToTenantRelProperties = (
        TenableAssetSourceToTenantRelProperties()
    )


@dataclass(frozen=True)
class TenableAssetSourceToAssetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableAsset)-[:HAS_SOURCE]->(:TenableAssetSource)
@dataclass(frozen=True)
class TenableAssetSourceToAssetRel(CartographyRelSchema):
    target_node_label: str = "TenableAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("asset_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SOURCE"
    properties: TenableAssetSourceToAssetRelProperties = (
        TenableAssetSourceToAssetRelProperties()
    )


@dataclass(frozen=True)
class TenableAssetSourceSchema(CartographyNodeSchema):
    label: str = "TenableAssetSource"
    properties: TenableAssetSourceNodeProperties = TenableAssetSourceNodeProperties()
    sub_resource_relationship: TenableAssetSourceToTenantRel = (
        TenableAssetSourceToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TenableAssetSourceToAssetRel(),
        ]
    )
