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
class VercelEdgeConfigNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    item_count: PropertyRef = PropertyRef("itemCount")
    size_in_bytes: PropertyRef = PropertyRef("sizeInBytes")
    digest: PropertyRef = PropertyRef("digest")


@dataclass(frozen=True)
class VercelEdgeConfigToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelEdgeConfig)
class VercelEdgeConfigToTeamRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelEdgeConfigToTeamRelProperties = (
        VercelEdgeConfigToTeamRelProperties()
    )


@dataclass(frozen=True)
class VercelEdgeConfigSchema(CartographyNodeSchema):
    label: str = "VercelEdgeConfig"
    properties: VercelEdgeConfigNodeProperties = VercelEdgeConfigNodeProperties()
    sub_resource_relationship: VercelEdgeConfigToTeamRel = VercelEdgeConfigToTeamRel()
