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
    id: PropertyRef = PropertyRef("id", description="Tenable tag UUID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    key: PropertyRef = PropertyRef(
        "key", extra_index=True, description="Tag category or key."
    )
    value: PropertyRef = PropertyRef("value", description="Tag value.")
    # DEPRECATED: will be deleted in version 1.0.0
    tag_key: PropertyRef = PropertyRef(
        "key", description="Deprecated mirror of key; removed in v1.0.0."
    )
    # DEPRECATED: will be deleted in version 1.0.0
    tag_value: PropertyRef = PropertyRef(
        "value", description="Deprecated mirror of value; removed in v1.0.0."
    )
    added_by: PropertyRef = PropertyRef(
        "added_by", description="User who applied the tag."
    )
    added_at: PropertyRef = PropertyRef(
        "added_at", description="Timestamp when the tag was applied."
    )


@dataclass(frozen=True)
class TenableAssetTagToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableAssetTag)
@dataclass(frozen=True)
class TenableAssetTagToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to one of its asset tags."""

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
    """Deprecated compatibility edge linking an asset to a tag until v1.0.0."""

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
    """Links a Tenable asset to a tag applied to it."""

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
    """A key-value tag applied to a Tenable asset."""

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
