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
class VercelEnvironmentVariableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    target: PropertyRef = PropertyRef("target")
    git_branch: PropertyRef = PropertyRef("gitBranch")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    edge_config_id: PropertyRef = PropertyRef("edgeConfigId")
    comment: PropertyRef = PropertyRef("comment")
    # NOTE: value is intentionally omitted — never store secrets


@dataclass(frozen=True)
class VercelEnvVarToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProject)-[:RESOURCE]->(:VercelEnvironmentVariable)
class VercelEnvVarToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelEnvVarToProjectRelProperties = (
        VercelEnvVarToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelEnvVarToEdgeConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelEnvironmentVariable)-[:REFERENCES]->(:VercelEdgeConfig)
class VercelEnvVarToEdgeConfigRel(CartographyRelSchema):
    target_node_label: str = "VercelEdgeConfig"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("edgeConfigId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES"
    properties: VercelEnvVarToEdgeConfigRelProperties = (
        VercelEnvVarToEdgeConfigRelProperties()
    )


@dataclass(frozen=True)
class VercelEnvironmentVariableSchema(CartographyNodeSchema):
    label: str = "VercelEnvironmentVariable"
    properties: VercelEnvironmentVariableNodeProperties = (
        VercelEnvironmentVariableNodeProperties()
    )
    sub_resource_relationship: VercelEnvVarToProjectRel = VercelEnvVarToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelEnvVarToEdgeConfigRel()],
    )
