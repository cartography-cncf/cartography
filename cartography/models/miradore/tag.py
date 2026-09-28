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
class MiradoreTagNodeProperties(CartographyNodeProperties):
    # The Miradore Tag item exposes a name and nothing else, so the name is the natural
    # key. It is still only unique within a tenant, hence the site name prefix.
    id: PropertyRef = PropertyRef(
        "id",
        description="Tenant-scoped identifier for the tag, as `<site name>/<tag name>`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Tag name.",
    )


@dataclass(frozen=True)
class MiradoreTagToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:MiradoreTenant)-[:RESOURCE]->(:MiradoreTag)
@dataclass(frozen=True)
class MiradoreTagToTenantRel(CartographyRelSchema):
    """Links a Miradore tenant to one of its tags."""

    target_node_label: str = "MiradoreTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: MiradoreTagToTenantRelProperties = MiradoreTagToTenantRelProperties()


@dataclass(frozen=True)
class MiradoreTagSchema(CartographyNodeSchema):
    """A tag that can be assigned to Miradore devices and users."""

    label: str = "MiradoreTag"
    properties: MiradoreTagNodeProperties = MiradoreTagNodeProperties()
    sub_resource_relationship: MiradoreTagToTenantRel = MiradoreTagToTenantRel()
