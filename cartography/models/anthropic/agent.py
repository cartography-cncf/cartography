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
class AnthropicAgentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic managed agent ID.")
    name: PropertyRef = PropertyRef("name", description="Agent name.")
    description: PropertyRef = PropertyRef(
        "description", description="What the agent is for."
    )
    version: PropertyRef = PropertyRef(
        "version", description="Monotonic version of the agent definition."
    )
    model_id: PropertyRef = PropertyRef(
        "model.id", description="Model the agent runs on."
    )
    model_effort: PropertyRef = PropertyRef(
        "model.effort", description="Reasoning effort the agent runs at."
    )
    mcp_server_urls: PropertyRef = PropertyRef(
        "mcp_server_urls",
        description=(
            "URLs of the MCP servers the agent connects to. Each one is an external "
            "system the agent can reach."
        ),
    )
    always_allow_tools: PropertyRef = PropertyRef(
        "always_allow_tools",
        description=(
            "Tools the agent may invoke without asking. These run unsupervised, so "
            "they carry the agent's full blast radius."
        ),
    )
    always_ask_tools: PropertyRef = PropertyRef(
        "always_ask_tools",
        description="Tools the agent must get confirmation for before invoking.",
    )
    archived_at: PropertyRef = PropertyRef(
        "archived_at",
        description=(
            "RFC 3339 timestamp when the agent was archived. Empty while it is live."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="RFC 3339 timestamp when the agent was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="RFC 3339 timestamp when the agent was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicAgentToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicWorkspace)-[:RESOURCE]->(:AnthropicAgent)
class AnthropicAgentToWorkspaceRel(CartographyRelSchema):
    """The workspace the agent belongs to."""

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicAgentToWorkspaceRelProperties = (
        AnthropicAgentToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicAgentToSkillRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicAgent)-[:USES_SKILL]->(:AnthropicSkill)
class AnthropicAgentToSkillRel(CartographyRelSchema):
    """A skill the agent has loaded."""

    target_node_label: str = "AnthropicSkill"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("skill_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SKILL"
    properties: AnthropicAgentToSkillRelProperties = (
        AnthropicAgentToSkillRelProperties()
    )


@dataclass(frozen=True)
class AnthropicAgentSchema(CartographyNodeSchema):
    """A managed agent defined in an Anthropic workspace."""

    label: str = "AnthropicAgent"
    properties: AnthropicAgentNodeProperties = AnthropicAgentNodeProperties()
    sub_resource_relationship: AnthropicAgentToWorkspaceRel = (
        AnthropicAgentToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicAgentToSkillRel(),
        ],
    )
