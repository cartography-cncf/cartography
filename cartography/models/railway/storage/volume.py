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
class RailwayVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    project_id: PropertyRef = PropertyRef("projectId", extra_index=True)
    created_at: PropertyRef = PropertyRef("createdAt")


@dataclass(frozen=True)
class RailwayVolumeToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayVolume)
class RailwayVolumeToProjectRel(CartographyRelSchema):
    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayVolumeToProjectRelProperties = (
        RailwayVolumeToProjectRelProperties()
    )


@dataclass(frozen=True)
# The project-scoped volume definition. The actual disk, with its size, region and state,
# is the per-environment RailwayVolumeInstance.
class RailwayVolumeSchema(CartographyNodeSchema):
    label: str = "RailwayVolume"
    properties: RailwayVolumeNodeProperties = RailwayVolumeNodeProperties()
    sub_resource_relationship: RailwayVolumeToProjectRel = RailwayVolumeToProjectRel()
