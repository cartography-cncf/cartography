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
class TenableAssetTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key", extra_index=True)
    value: PropertyRef = PropertyRef("value")
    # DEPRECATED: will be deleted in version 1.0.0
    tag_key: PropertyRef = PropertyRef("key")
    # DEPRECATED: will be deleted in version 1.0.0
    tag_value: PropertyRef = PropertyRef("value")
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


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
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
class TenableAssetTagToAssetTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableAsset)-[:TAGGED]->(:TenableAssetTag)
@dataclass(frozen=True)
class TenableAssetTagToAssetTaggedRel(CartographyRelSchema):
    target_node_label: str = "TenableAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("asset_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: TenableAssetTagToAssetTaggedRelProperties = (
        TenableAssetTagToAssetTaggedRelProperties()
    )


@dataclass(frozen=True)
class TenableAssetTagSchema(CartographyNodeSchema):
    label: str = "TenableAssetTag"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tag"])
    properties: TenableAssetTagNodeProperties = TenableAssetTagNodeProperties()
    sub_resource_relationship: TenableAssetTagToTenantRel = TenableAssetTagToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TenableAssetTagToAssetRel(),
            TenableAssetTagToAssetTaggedRel(),
        ]
    )
