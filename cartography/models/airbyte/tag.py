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
class AirbyteTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("tagId", description="Tag UUID.")
    name: PropertyRef = PropertyRef("name", description="Tag name.")
    color: PropertyRef = PropertyRef("color", description="Tag color in hexadecimal.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class AirbyteTagToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteTag)
class AirbyteTagToOrganizationRel(CartographyRelSchema):
    """Links an organization to a tag it owns."""

    target_node_label: str = "AirbyteOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AirbyteTagToOrganizationRelProperties = (
        AirbyteTagToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AirbyteTagToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AirbyteWorkspace)-[:CONTAINS]->(:AirbyteTag)
class AirbyteTagToWorkspaceRel(CartographyRelSchema):
    """Links a workspace to a tag it contains."""

    target_node_label: str = "AirbyteWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspaceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AirbyteTagToWorkspaceRelProperties = (
        AirbyteTagToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AirbyteTagSchema(CartographyNodeSchema):
    """A tag used to categorize Airbyte resources."""

    label: str = "AirbyteTag"
    properties: AirbyteTagNodeProperties = AirbyteTagNodeProperties()
    sub_resource_relationship: AirbyteTagToOrganizationRel = (
        AirbyteTagToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [AirbyteTagToWorkspaceRel()]
    )
