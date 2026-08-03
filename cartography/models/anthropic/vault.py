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
class AnthropicVaultNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic vault ID.")
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Vault name shown in the Console."
    )
    archived_at: PropertyRef = PropertyRef(
        "archived_at",
        description="RFC 3339 timestamp when the vault was archived. Empty while live.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="RFC 3339 timestamp when the vault was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="RFC 3339 timestamp when the vault was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicVaultToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicWorkspace)-[:RESOURCE]->(:AnthropicVault)
class AnthropicVaultToWorkspaceRel(CartographyRelSchema):
    """The workspace the vault belongs to."""

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicVaultToWorkspaceRelProperties = (
        AnthropicVaultToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicVaultSchema(CartographyNodeSchema):
    """A container of credentials that agent sessions and deployments can draw on.

    Only the vault itself is enumerable; the secrets inside it are not exposed by
    the API, so the graph records which workloads can reach a vault, not what is in
    it.
    """

    label: str = "AnthropicVault"
    properties: AnthropicVaultNodeProperties = AnthropicVaultNodeProperties()
    sub_resource_relationship: AnthropicVaultToWorkspaceRel = (
        AnthropicVaultToWorkspaceRel()
    )
