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
class RailwayServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    icon: PropertyRef = PropertyRef("icon")
    project_id: PropertyRef = PropertyRef("projectId", extra_index=True)
    template_id: PropertyRef = PropertyRef("templateId")
    is_restricted: PropertyRef = PropertyRef("isRestricted")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class RailwayServiceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayService)
class RailwayServiceToProjectRel(CartographyRelSchema):
    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayServiceToProjectRelProperties = (
        RailwayServiceToProjectRelProperties()
    )


@dataclass(frozen=True)
# A Service is the environment-agnostic shell. Every deployable attribute - source image or
# repo, region, replicas, domains - lives on the per-environment RailwayServiceInstance
# instead, so this node carries no semantic ontology label of its own.
class RailwayServiceSchema(CartographyNodeSchema):
    label: str = "RailwayService"
    properties: RailwayServiceNodeProperties = RailwayServiceNodeProperties()
    sub_resource_relationship: RailwayServiceToProjectRel = RailwayServiceToProjectRel()
