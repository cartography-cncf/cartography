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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    label: PropertyRef = PropertyRef("label", extra_index=True)
    created_at: PropertyRef = PropertyRef("createdAt")
    # NOTE: token value is intentionally omitted — never store secrets


@dataclass(frozen=True)
class VercelEdgeConfigTokenToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelEdgeConfigToken)
class VercelEdgeConfigTokenToTeamRel(CartographyRelSchema):
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
