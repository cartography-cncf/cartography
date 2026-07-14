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
class VercelProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Project ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Project name."
    )
    framework: PropertyRef = PropertyRef(
        "framework", description="Framework preset used by the project."
    )
    node_version: PropertyRef = PropertyRef(
        "nodeVersion", description="Node.js version used by the project."
    )
    build_command: PropertyRef = PropertyRef(
        "buildCommand", description="Build command override."
    )
    dev_command: PropertyRef = PropertyRef(
        "devCommand", description="Development command override."
    )
    install_command: PropertyRef = PropertyRef(
        "installCommand", description="Install command override."
    )
    output_directory: PropertyRef = PropertyRef(
        "outputDirectory", description="Build output directory."
    )
    public_source: PropertyRef = PropertyRef(
        "publicSource", description="Whether the project source is publicly viewable."
    )
    serverless_function_region: PropertyRef = PropertyRef(
        "serverlessFunctionRegion", description="Region where serverless functions run."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the project was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Timestamp when the project was last updated."
    )
    auto_expose_system_envs: PropertyRef = PropertyRef(
        "autoExposeSystemEnvs",
        description="Whether system environment variables are exposed automatically.",
    )
    root_directory: PropertyRef = PropertyRef(
        "rootDirectory", description="Root directory of the project."
    )
    git_fork_protection: PropertyRef = PropertyRef(
        "gitForkProtection",
        description="Whether fork protection is enabled for Git deployments.",
    )
    skew_protection_max_age: PropertyRef = PropertyRef(
        "skewProtectionMaxAge",
        description="Maximum deployment age retained for skew protection.",
    )


@dataclass(frozen=True)
class VercelProjectToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelProject)
class VercelProjectToTeamRel(CartographyRelSchema):
    """The Vercel team contains this project as a resource."""

    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelProjectToTeamRelProperties = VercelProjectToTeamRelProperties()


@dataclass(frozen=True)
class VercelProjectSchema(CartographyNodeSchema):
    """A project managed by Vercel."""

    label: str = "VercelProject"
    properties: VercelProjectNodeProperties = VercelProjectNodeProperties()
    sub_resource_relationship: VercelProjectToTeamRel = VercelProjectToTeamRel()
