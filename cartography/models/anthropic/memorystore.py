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
class AnthropicMemoryStoreNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic memory store ID.")
    name: PropertyRef = PropertyRef("name", description="Memory store name.")
    description: PropertyRef = PropertyRef(
        "description", description="What the memory store holds."
    )
    archived_at: PropertyRef = PropertyRef(
        "archived_at",
        description=(
            "RFC 3339 timestamp when the memory store was archived. Empty while live."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the memory store was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the memory store was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicMemoryStoreToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicWorkspace)-[:RESOURCE]->(:AnthropicMemoryStore)
class AnthropicMemoryStoreToWorkspaceRel(CartographyRelSchema):
    """The workspace the memory store belongs to."""

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicMemoryStoreToWorkspaceRelProperties = (
        AnthropicMemoryStoreToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicMemoryStoreSchema(CartographyNodeSchema):
    """Persistent memory an agent carries between sessions."""

    label: str = "AnthropicMemoryStore"
    properties: AnthropicMemoryStoreNodeProperties = (
        AnthropicMemoryStoreNodeProperties()
    )
    sub_resource_relationship: AnthropicMemoryStoreToWorkspaceRel = (
        AnthropicMemoryStoreToWorkspaceRel()
    )
