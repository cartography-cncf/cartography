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
class MiradoreOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Tenant-scoped identifier for the organization, as `<site name>/<Miradore ID>`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    miradore_id: PropertyRef = PropertyRef(
        "miradore_id",
        extra_index=True,
        description="Raw Miradore ID of the organization, which is only unique within the tenant.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Organization name.",
    )
    full_name: PropertyRef = PropertyRef(
        "full_name",
        description="Fully qualified organization name including its ancestors.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Organization status: Unknown, Active or Removed.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="Timestamp when the organization was created.",
    )
    modified: PropertyRef = PropertyRef(
        "modified",
        description="Timestamp when the organization was last modified.",
    )


@dataclass(frozen=True)
class MiradoreOrganizationToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreTenant)-[:RESOURCE]->(:MiradoreOrganization)
@dataclass(frozen=True)
class MiradoreOrganizationToTenantRel(CartographyRelSchema):
    """Links a Miradore tenant to one of its organizations."""

    target_node_label: str = "MiradoreTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: MiradoreOrganizationToTenantRelProperties = (
        MiradoreOrganizationToTenantRelProperties()
    )


@dataclass(frozen=True)
class MiradoreOrganizationToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreOrganization)-[:MEMBER_OF]->(:MiradoreOrganization)
@dataclass(frozen=True)
class MiradoreOrganizationToParentRel(CartographyRelSchema):
    """Links a Miradore organization to its parent organization."""

    target_node_label: str = "MiradoreOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: MiradoreOrganizationToParentRelProperties = (
        MiradoreOrganizationToParentRelProperties()
    )


@dataclass(frozen=True)
class MiradoreOrganizationSchema(CartographyNodeSchema):
    """An organization unit in the Miradore organization hierarchy."""

    label: str = "MiradoreOrganization"
    properties: MiradoreOrganizationNodeProperties = (
        MiradoreOrganizationNodeProperties()
    )
    sub_resource_relationship: MiradoreOrganizationToTenantRel = (
        MiradoreOrganizationToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [MiradoreOrganizationToParentRel()],
    )
