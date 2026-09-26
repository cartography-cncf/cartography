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
class LangSmithMcpServerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="MCP server or gateway UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="MCP server name."
    )
    slug: PropertyRef = PropertyRef("slug", description="MCP server slug.")
    description: PropertyRef = PropertyRef(
        "description", description="Human-readable description of the MCP server."
    )
    url: PropertyRef = PropertyRef(
        "url", description="URL the MCP server is served from."
    )
    vendor: PropertyRef = PropertyRef(
        "vendor",
        description="MCP vendor fronting this server, when it is a vendor-managed gateway.",
    )
    auth_type: PropertyRef = PropertyRef(
        "auth_type",
        description="How callers authenticate to this MCP server, for example oauth or none.",
    )
    status: PropertyRef = PropertyRef("status", description="MCP server status.")
    tool_names: PropertyRef = PropertyRef(
        "tool_names",
        description="Names of the tools this MCP server exposes, where the API reports them.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the MCP server was registered."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the MCP server was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithMcpServerToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithMcpServer)
class LangSmithMcpServerToOrganizationRel(CartographyRelSchema):
    """Links an organization to an MCP server registered within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithMcpServerToOrganizationRelProperties = (
        LangSmithMcpServerToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithMcpServerToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:CONTAINS]->(:LangSmithMcpServer)
class LangSmithMcpServerToWorkspaceRel(CartographyRelSchema):
    """Links an MCP server to the workspace that exposes it."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: LangSmithMcpServerToWorkspaceRelProperties = (
        LangSmithMcpServerToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithMcpServerSchema(CartographyNodeSchema):
    """An MCP server a LangSmith workspace exposes to its agents."""

    label: str = "LangSmithMcpServer"
    properties: LangSmithMcpServerNodeProperties = LangSmithMcpServerNodeProperties()
    sub_resource_relationship: LangSmithMcpServerToOrganizationRel = (
        LangSmithMcpServerToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithMcpServerToWorkspaceRel(),
        ],
    )
