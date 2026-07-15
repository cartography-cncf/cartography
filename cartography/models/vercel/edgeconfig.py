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
    id: PropertyRef = PropertyRef("id", description="Edge Config ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    slug: PropertyRef = PropertyRef(
        "slug", extra_index=True, description="Edge Config slug."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the Edge Config was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Timestamp when the Edge Config was last updated."
    )
    item_count: PropertyRef = PropertyRef(
        "itemCount", description="Number of items in the Edge Config."
    )
    size_in_bytes: PropertyRef = PropertyRef(
        "sizeInBytes", description="Size of the Edge Config in bytes."
    )
    digest: PropertyRef = PropertyRef(
        "digest", description="Content digest of the Edge Config."
    )


@dataclass(frozen=True)
class VercelEdgeConfigToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelEdgeConfig)
class VercelEdgeConfigToTeamRel(CartographyRelSchema):
    """The Vercel team contains this Edge Config as a resource."""

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
    """A Vercel Edge Config that serves runtime data from the edge."""

    label: str = "VercelEdgeConfig"
    properties: VercelEdgeConfigNodeProperties = VercelEdgeConfigNodeProperties()
    sub_resource_relationship: VercelEdgeConfigToTeamRel = VercelEdgeConfigToTeamRel()
