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
    id: PropertyRef = PropertyRef("id", description="Environment variable ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    key: PropertyRef = PropertyRef(
        "key", extra_index=True, description="Environment variable name."
    )
    type: PropertyRef = PropertyRef("type", description="Environment variable type.")
    target: PropertyRef = PropertyRef(
        "target", description="Target environments for the variable."
    )
    git_branch: PropertyRef = PropertyRef(
        "gitBranch", description="Git branch scope for the variable."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the variable was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Timestamp when the variable was last updated."
    )
    edge_config_id: PropertyRef = PropertyRef(
        "edgeConfigId", description="ID of the referenced Edge Config, if any."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Optional description of the variable."
    )
    # NOTE: Value is intentionally omitted to avoid storing secrets.


@dataclass(frozen=True)
class VercelEnvVarToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelProject)-[:RESOURCE]->(:VercelEnvironmentVariable)
class VercelEnvVarToProjectRel(CartographyRelSchema):
    """The Vercel project contains this environment variable as a resource."""

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
    """The Vercel environment variable references this Edge Config."""

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
    """A project-scoped Vercel environment variable whose value is not stored."""

    label: str = "VercelEnvironmentVariable"
    properties: VercelEnvironmentVariableNodeProperties = (
        VercelEnvironmentVariableNodeProperties()
    )
    sub_resource_relationship: VercelEnvVarToProjectRel = VercelEnvVarToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelEnvVarToEdgeConfigRel()],
    )
