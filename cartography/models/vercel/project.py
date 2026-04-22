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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    framework: PropertyRef = PropertyRef("framework")
    node_version: PropertyRef = PropertyRef("nodeVersion")
    build_command: PropertyRef = PropertyRef("buildCommand")
    dev_command: PropertyRef = PropertyRef("devCommand")
    install_command: PropertyRef = PropertyRef("installCommand")
    output_directory: PropertyRef = PropertyRef("outputDirectory")
    public_source: PropertyRef = PropertyRef("publicSource")
    serverless_function_region: PropertyRef = PropertyRef("serverlessFunctionRegion")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    auto_expose_system_envs: PropertyRef = PropertyRef("autoExposeSystemEnvs")
    root_directory: PropertyRef = PropertyRef("rootDirectory")
    git_fork_protection: PropertyRef = PropertyRef("gitForkProtection")
    skew_protection_max_age: PropertyRef = PropertyRef("skewProtectionMaxAge")


@dataclass(frozen=True)
class VercelProjectToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelProject)
class VercelProjectToTeamRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelProjectToTeamRelProperties = VercelProjectToTeamRelProperties()


@dataclass(frozen=True)
class VercelProjectSchema(CartographyNodeSchema):
    label: str = "VercelProject"
    properties: VercelProjectNodeProperties = VercelProjectNodeProperties()
    sub_resource_relationship: VercelProjectToTeamRel = VercelProjectToTeamRel()
