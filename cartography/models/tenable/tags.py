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
class TenableAssetTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    tag_key: PropertyRef = PropertyRef("tag_key")
    tag_value: PropertyRef = PropertyRef("tag_value")
    added_by: PropertyRef = PropertyRef("added_by")
    added_at: PropertyRef = PropertyRef("added_at")


@dataclass(frozen=True)
class TenableAssetTagToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAssetTag)
@dataclass(frozen=True)
class TenableAssetTagToTenantRel(CartographyRelSchema):
    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableAssetTagToTenantRelProperties = (
        TenableAssetTagToTenantRelProperties()
    )


@dataclass(frozen=True)
class TenableAssetTagToAssetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableAsset)-[:HAS_TAG]->(:TenableAssetTag)
@dataclass(frozen=True)
class TenableAssetTagToAssetRel(CartographyRelSchema):
    target_node_label: str = "TenableAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("asset_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TAG"
    properties: TenableAssetTagToAssetRelProperties = (
        TenableAssetTagToAssetRelProperties()
    )


@dataclass(frozen=True)
class TenableAssetTagSchema(CartographyNodeSchema):
    label: str = "TenableAssetTag"
    properties: TenableAssetTagNodeProperties = TenableAssetTagNodeProperties()
    sub_resource_relationship: TenableAssetTagToTenantRel = TenableAssetTagToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TenableAssetTagToAssetRel(),
        ]
    )
