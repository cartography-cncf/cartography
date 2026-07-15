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
class VercelEdgeConfigTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Edge Config token ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    label: PropertyRef = PropertyRef(
        "label", extra_index=True, description="Edge Config token label."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the Edge Config token was created."
    )
    # NOTE: The token value is intentionally omitted to avoid storing secrets.


@dataclass(frozen=True)
class VercelEdgeConfigTokenToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelEdgeConfigToken)
class VercelEdgeConfigTokenToTeamRel(CartographyRelSchema):
    """The Vercel team contains this Edge Config token as a resource."""

    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelEdgeConfigTokenToTeamRelProperties = (
        VercelEdgeConfigTokenToTeamRelProperties()
    )


@dataclass(frozen=True)
class VercelEdgeConfigTokenToEdgeConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelEdgeConfig)-[:HAS_TOKEN]->(:VercelEdgeConfigToken)
class VercelEdgeConfigTokenToEdgeConfigRel(CartographyRelSchema):
    """The Vercel Edge Config exposes this access token."""

    target_node_label: str = "VercelEdgeConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("edge_config_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TOKEN"
    properties: VercelEdgeConfigTokenToEdgeConfigRelProperties = (
        VercelEdgeConfigTokenToEdgeConfigRelProperties()
    )


@dataclass(frozen=True)
class VercelEdgeConfigTokenSchema(CartographyNodeSchema):
    """A Vercel read token that grants access to an Edge Config."""

    label: str = "VercelEdgeConfigToken"
    properties: VercelEdgeConfigTokenNodeProperties = (
        VercelEdgeConfigTokenNodeProperties()
    )
    sub_resource_relationship: VercelEdgeConfigTokenToTeamRel = (
        VercelEdgeConfigTokenToTeamRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelEdgeConfigTokenToEdgeConfigRel()],
    )
