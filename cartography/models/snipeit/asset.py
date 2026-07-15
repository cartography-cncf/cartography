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
class SnipeitAssetNodeProperties(CartographyNodeProperties):
    """
    https://snipe-it.readme.io/reference/hardware-list
    """

    # Common properties
    id: PropertyRef = PropertyRef("id", description="Asset ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )

    # SnipeIT specific properties
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Device name.",
    )
    asset_tag: PropertyRef = PropertyRef("asset_tag", description="Asset tag.")
    assigned_to: PropertyRef = PropertyRef(
        "assigned_to.email",
        description="Email of the user who checked out the asset.",
    )
    category: PropertyRef = PropertyRef(
        "category.name",
        description="Asset category.",
    )
    company: PropertyRef = PropertyRef(
        "company.name",
        description="Company that owns the asset.",
    )
    manufacturer: PropertyRef = PropertyRef(
        "manufacturer.name",
        description="Asset manufacturer.",
    )
    model: PropertyRef = PropertyRef("model.name", description="Device model.")
    serial: PropertyRef = PropertyRef(
        "serial",
        extra_index=True,
        description="Asset serial number.",
    )
    status: PropertyRef = PropertyRef(
        "status_label.name",
        description="Asset status label.",
    )


# (:SnipeitAsset)<-[:RESOURCE]-(:SnipeitTenant)
@dataclass(frozen=True)
class SnipeitTenantToSnipeitAssetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SnipeitTenantToSnipeitAssetRel(CartographyRelSchema):
    """The tenant contains the asset."""

    target_node_label: str = "SnipeitTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnipeitTenantToSnipeitAssetRelProperties = (
        SnipeitTenantToSnipeitAssetRelProperties()
    )


# (:SnipeitUser)-[:HAS_CHECKED_OUT]->(:SnipeitAsset)
@dataclass(frozen=True)
class SnipeitUserToSnipeitAssetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SnipeitUserToSnipeitAssetRel(CartographyRelSchema):
    """A user has checked out the asset."""

    target_node_label: str = "SnipeitUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("assigned_to.email")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CHECKED_OUT"
    properties: SnipeitUserToSnipeitAssetRelProperties = (
        SnipeitUserToSnipeitAssetRelProperties()
    )


@dataclass(frozen=True)
# (:SnipeitAsset)<-[:HAS_ASSET]-(:SnipeitTenant) - Backwards compatibility
class SnipeitTenantToSnipeitAssetDeprecatedRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a tenant to its asset."""

    target_node_label: str = "SnipeitTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ASSET"
    properties: SnipeitTenantToSnipeitAssetRelProperties = (
        SnipeitTenantToSnipeitAssetRelProperties()
    )


@dataclass(frozen=True)
class SnipeitAssetSchema(CartographyNodeSchema):
    """A device asset managed by Snipe-IT."""

    label: str = "SnipeitAsset"  # The label of the node
    properties: SnipeitAssetNodeProperties = (
        SnipeitAssetNodeProperties()
    )  # An object representing all properties
    sub_resource_relationship: SnipeitTenantToSnipeitAssetRel = (
        SnipeitTenantToSnipeitAssetRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnipeitUserToSnipeitAssetRel(),
            # DEPRECATED: for backward compatibility, will be removed in v1.0.0
            SnipeitTenantToSnipeitAssetDeprecatedRel(),
        ],
    )
