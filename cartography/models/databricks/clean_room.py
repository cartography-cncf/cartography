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
class DatabricksCleanRoomNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    access_restricted: PropertyRef = PropertyRef("access_restricted")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksCleanRoomToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksCleanRoom)
class DatabricksCleanRoomToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksCleanRoomToWorkspaceRelProperties = (
        DatabricksCleanRoomToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksCleanRoomSchema(CartographyNodeSchema):
    label: str = "DatabricksCleanRoom"
    properties: DatabricksCleanRoomNodeProperties = DatabricksCleanRoomNodeProperties()
    sub_resource_relationship: DatabricksCleanRoomToWorkspaceRel = (
        DatabricksCleanRoomToWorkspaceRel()
    )
