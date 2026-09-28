from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class MiradoreConfigProfileNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Tenant-scoped identifier for the configuration profile, as `<site name>/<Miradore ID>`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    miradore_id: PropertyRef = PropertyRef(
        "miradore_id",
        extra_index=True,
        description="Raw Miradore ID of the configuration profile, which is only unique within the tenant.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Configuration profile name.",
    )
    configuration_type: PropertyRef = PropertyRef(
        "configuration_type",
        description="Type of configuration carried by the profile.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Configuration profile description.",
    )
    os_category: PropertyRef = PropertyRef(
        "os_category",
        # The API specification documents Android, iOS and WindowsPhone, but a live
        # tenant also returns WindowsDesktop and macOS, so treat this as open-ended.
        description="Platform the profile targets, e.g. Android, iOS, macOS or WindowsDesktop.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Profile status: Unknown, Active or Deleted.",
    )


@dataclass(frozen=True)
class MiradoreConfigProfileToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreTenant)-[:RESOURCE]->(:MiradoreConfigProfile)
@dataclass(frozen=True)
class MiradoreConfigProfileToTenantRel(CartographyRelSchema):
    """Links a Miradore tenant to one of its configuration profiles."""

    target_node_label: str = "MiradoreTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: MiradoreConfigProfileToTenantRelProperties = (
        MiradoreConfigProfileToTenantRelProperties()
    )


@dataclass(frozen=True)
class MiradoreConfigProfileSchema(CartographyNodeSchema):
    """An MDM configuration profile defined in Miradore."""

    label: str = "MiradoreConfigProfile"
    properties: MiradoreConfigProfileNodeProperties = (
        MiradoreConfigProfileNodeProperties()
    )
    sub_resource_relationship: MiradoreConfigProfileToTenantRel = (
        MiradoreConfigProfileToTenantRel()
    )
