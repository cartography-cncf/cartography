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
class ScalewayApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    editable: PropertyRef = PropertyRef("editable")
    deletable: PropertyRef = PropertyRef("deletable")
    managed: PropertyRef = PropertyRef("managed")
    tags: PropertyRef = PropertyRef("tags")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayApplicationToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayApplication)
class ScalewayApplicationToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayApplicationToOrganizationRelProperties = (
        ScalewayApplicationToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayApplicationSchema(CartographyNodeSchema):
    label: str = "ScalewayApplication"
    properties: ScalewayApplicationNodeProperties = ScalewayApplicationNodeProperties()
    sub_resource_relationship: ScalewayApplicationToOrganizationRel = (
        ScalewayApplicationToOrganizationRel()
    )
