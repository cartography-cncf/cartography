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
class KonnectControlPlaneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")


@dataclass(frozen=True)
class KonnectControlPlaneToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KonnectControlPlane)-[:RESOURCE]->(:KonnectOrganization)
class KonnectControlPlaneToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "KonnectOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: KonnectControlPlaneToOrganizationRelProperties = (
        KonnectControlPlaneToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class KonnectControlPlaneSchema(CartographyNodeSchema):
    label: str = "KonnectControlPlane"
    properties: KonnectControlPlaneNodeProperties = KonnectControlPlaneNodeProperties()
    sub_resource_relationship: KonnectControlPlaneToOrganizationRel = (
        KonnectControlPlaneToOrganizationRel()
    )
