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
class ScalewayGroupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Group")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Date and time of group creation."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Date and time of last group update."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the group.")
    description: PropertyRef = PropertyRef(
        "description", description="Description of the group."
    )
    tags: PropertyRef = PropertyRef(
        "tags", extra_index=True, description="Tags associated to the group."
    )
    editable: PropertyRef = PropertyRef(
        "editable", description="Defines whether or not the group is editable."
    )
    deletable: PropertyRef = PropertyRef(
        "deletable", description="Defines whether or not the group is deletable."
    )
    managed: PropertyRef = PropertyRef(
        "managed", description="Defines whether or not the group is managed."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayUser)-[:MEMBER_OF]->(:ScalewayGroup)
class ScalewayGroupToUserRel(CartographyRelSchema):
    """Connects `ScalewayUser` to `ScalewayGroup` through `MEMBER_OF`."""

    target_node_label: str = "ScalewayUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: ScalewayGroupToUserRelProperties = ScalewayGroupToUserRelProperties()


@dataclass(frozen=True)
class ScalewayGroupToApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayApplication)-[:MEMBER_OF]->(:ScalewayGroup)
class ScalewayGroupToApplicationRel(CartographyRelSchema):
    """Connects `ScalewayApplication` to `ScalewayGroup` through `MEMBER_OF`."""

    target_node_label: str = "ScalewayApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("application_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: ScalewayGroupToApplicationRelProperties = (
        ScalewayGroupToApplicationRelProperties()
    )


@dataclass(frozen=True)
class ScalewayGroupToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayOrganization)-[:RESOURCE]->(:ScalewayGroup)
class ScalewayGroupToOrganizationRel(CartographyRelSchema):
    """Connects `ScalewayOrganization` to `ScalewayGroup` through `RESOURCE`."""

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
    """Represents a Group in Scaleway."""

    label: str = "ScalewayGroup"
    properties: ScalewayGroupProperties = ScalewayGroupProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    sub_resource_relationship: ScalewayGroupToOrganizationRel = (
        ScalewayGroupToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayGroupToUserRel(),
            ScalewayGroupToApplicationRel(),
        ]
    )
