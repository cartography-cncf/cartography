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
class MiradoreLocationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Tenant-scoped identifier for the location, as `<site name>/<Miradore ID>`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    miradore_id: PropertyRef = PropertyRef(
        "miradore_id",
        extra_index=True,
        description="Raw Miradore ID of the location, which is only unique within the tenant.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Location name.",
    )
    full_name: PropertyRef = PropertyRef(
        "full_name",
        description="Fully qualified location name including its ancestors.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Location status: Unknown, Active or Removed.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Timestamp when the location was created.",
    )
    modified: PropertyRef = PropertyRef(
        "modified",
        description="Timestamp when the location was last modified.",
    )


@dataclass(frozen=True)
class MiradoreLocationToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreTenant)-[:RESOURCE]->(:MiradoreLocation)
@dataclass(frozen=True)
class MiradoreLocationToTenantRel(CartographyRelSchema):
    """Links a Miradore tenant to one of its locations."""

    target_node_label: str = "MiradoreTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: MiradoreLocationToTenantRelProperties = (
        MiradoreLocationToTenantRelProperties()
    )


@dataclass(frozen=True)
class MiradoreLocationToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreLocation)-[:MEMBER_OF]->(:MiradoreLocation)
@dataclass(frozen=True)
class MiradoreLocationToParentRel(CartographyRelSchema):
    """Links a Miradore location to its parent location."""

    target_node_label: str = "MiradoreLocation"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: MiradoreLocationToParentRelProperties = (
        MiradoreLocationToParentRelProperties()
    )


@dataclass(frozen=True)
class MiradoreLocationSchema(CartographyNodeSchema):
    """A site in the Miradore location hierarchy."""

    label: str = "MiradoreLocation"
    properties: MiradoreLocationNodeProperties = MiradoreLocationNodeProperties()
    sub_resource_relationship: MiradoreLocationToTenantRel = (
        MiradoreLocationToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [MiradoreLocationToParentRel()],
    )
