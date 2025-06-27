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
class ScalewayGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    tags: PropertyRef = PropertyRef("tags", extra_index=True)
    editable: PropertyRef = PropertyRef("editable")
    deletable: PropertyRef = PropertyRef("deletable")
    managed: PropertyRef = PropertyRef("managed")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayGroupToUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayUser)-[:MEMBER_OF]->(:ScalewayGroup)
class ScalewayGroupToUserRel(CartographyRelSchema):
    target_node_label: str = "ScalewayUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: ScalewayGroupToUserProperties = ScalewayGroupToUserProperties()


@dataclass(frozen=True)
class ScalewayGroupToApplicationProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayApplication)-[:MEMBER_OF]->(:ScalewayGroup)
class ScalewayGroupToApplicationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: ScalewayGroupToApplicationProperties = (
        ScalewayGroupToApplicationProperties()
    )


@dataclass(frozen=True)
class ScalewayGroupToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayGroup)
class ScalewayGroupToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "ScalewayOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayGroupToOrganizationRelProperties = (
        ScalewayGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayGroupSchema(CartographyNodeSchema):
    label: str = "ScalewayGroup"
    properties: ScalewayGroupProperties = ScalewayGroupProperties()
    sub_resource_relationship: ScalewayGroupToOrganizationRel = (
        ScalewayGroupToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayGroupToUserRel(),
            ScalewayGroupToApplicationRel(),
        ]
    )
