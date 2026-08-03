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
class AnthropicSkillNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic skill ID.")
    display_title: PropertyRef = PropertyRef(
        "display_title",
        description="Skill title shown in the Console.",
    )
    source: PropertyRef = PropertyRef(
        "source",
        description=(
            "Who authored the skill: custom for one uploaded to this workspace, or "
            "anthropic for a first-party one available organization-wide."
        ),
    )
    latest_version: PropertyRef = PropertyRef(
        "latest_version",
        description="Version identifier of the most recent version.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the skill was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the skill was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicSkillToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicWorkspace)-[:RESOURCE]->(:AnthropicSkill)
class AnthropicSkillToWorkspaceRel(CartographyRelSchema):
    """The workspace the skill is available in."""

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicSkillToWorkspaceRelProperties = (
        AnthropicSkillToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicSkillSchema(CartographyNodeSchema):
    """A skill available to agents in an Anthropic workspace.

    Custom skills are private to the workspace that uploaded them. There is no
    organization-wide listing, so reaching them means a workspace-scoped credential
    per workspace.
    """

    label: str = "AnthropicSkill"
    properties: AnthropicSkillNodeProperties = AnthropicSkillNodeProperties()
    sub_resource_relationship: AnthropicSkillToWorkspaceRel = (
        AnthropicSkillToWorkspaceRel()
    )


@dataclass(frozen=True)
class AnthropicSkillVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic skill version ID.")
    name: PropertyRef = PropertyRef("name", description="Skill version name.")
    description: PropertyRef = PropertyRef(
        "description",
        description="What the skill does, as declared by this version.",
    )
    directory: PropertyRef = PropertyRef(
        "directory",
        description="Directory the skill's files are rooted at.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Version identifier, a microsecond epoch rendered as a string.",
    )
    skill_id: PropertyRef = PropertyRef(
        "skill_id",
        description="Skill this version belongs to.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the version was created.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicSkillVersionToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicWorkspace)-[:RESOURCE]->(:AnthropicSkillVersion)
class AnthropicSkillVersionToWorkspaceRel(CartographyRelSchema):
    """The workspace the skill version is available in."""

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicSkillVersionToWorkspaceRelProperties = (
        AnthropicSkillVersionToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicSkillVersionToSkillRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicSkill)-[:HAS_VERSION]->(:AnthropicSkillVersion)
class AnthropicSkillVersionToSkillRel(CartographyRelSchema):
    """The skill this version belongs to."""

    target_node_label: str = "AnthropicSkill"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("skill_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_VERSION"
    properties: AnthropicSkillVersionToSkillRelProperties = (
        AnthropicSkillVersionToSkillRelProperties()
    )


@dataclass(frozen=True)
class AnthropicSkillVersionSchema(CartographyNodeSchema):
    """A published version of an Anthropic skill."""

    label: str = "AnthropicSkillVersion"
    properties: AnthropicSkillVersionNodeProperties = (
        AnthropicSkillVersionNodeProperties()
    )
    sub_resource_relationship: AnthropicSkillVersionToWorkspaceRel = (
        AnthropicSkillVersionToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicSkillVersionToSkillRel(),
        ],
    )
