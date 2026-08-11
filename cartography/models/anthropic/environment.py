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
class AnthropicEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic environment ID.")
    name: PropertyRef = PropertyRef("name", description="Environment name.")
    description: PropertyRef = PropertyRef(
        "description", description="What the environment is for."
    )
    config_type: PropertyRef = PropertyRef(
        "config_type",
        description="Where agents run: cloud, or self_hosted on your own infrastructure.",
    )
    networking_type: PropertyRef = PropertyRef(
        "networking_type",
        description=(
            "Egress posture of the sandbox: unrestricted, or limited to an explicit "
            "allowlist. Empty for self-hosted environments, whose egress is governed "
            "by your own infrastructure."
        ),
    )
    allowed_hosts: PropertyRef = PropertyRef(
        "allowed_hosts",
        description="Hosts the sandbox may reach when networking is limited.",
    )
    allow_mcp_servers: PropertyRef = PropertyRef(
        "allow_mcp_servers",
        description="Whether a limited sandbox may still reach MCP servers.",
    )
    allow_package_managers: PropertyRef = PropertyRef(
        "allow_package_managers",
        description="Whether a limited sandbox may still reach package registries.",
    )
    scope: PropertyRef = PropertyRef(
        "scope",
        description="Whether the environment is shared organization-wide or per account.",
    )
    archived_at: PropertyRef = PropertyRef(
        "archived_at",
        description=(
            "RFC 3339 timestamp when the environment was archived. Empty while it is "
            "live."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="RFC 3339 timestamp when the environment was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the environment was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicEnvironmentToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicWorkspace)-[:RESOURCE]->(:AnthropicEnvironment)
class AnthropicEnvironmentToWorkspaceRel(CartographyRelSchema):
    """The workspace the environment belongs to."""

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicEnvironmentToWorkspaceRelProperties = (
        AnthropicEnvironmentToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicEnvironmentSchema(CartographyNodeSchema):
    """A sandbox agents execute in, and the egress policy that bounds them."""

    label: str = "AnthropicEnvironment"
    properties: AnthropicEnvironmentNodeProperties = (
        AnthropicEnvironmentNodeProperties()
    )
    sub_resource_relationship: AnthropicEnvironmentToWorkspaceRel = (
        AnthropicEnvironmentToWorkspaceRel()
    )
