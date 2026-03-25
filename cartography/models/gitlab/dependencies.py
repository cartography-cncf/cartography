"""
GitLab Dependency Schema

Represents individual dependencies declared in GitLab project dependency files.
A dependency is a library or package that a project depends on.
"""

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
class GitLabDependencyNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Dependency node.
    """

    id: PropertyRef = PropertyRef("id")  # Unique identifier
    name: PropertyRef = PropertyRef("name", extra_index=True)  # Canonicalized package name
    original_name: PropertyRef = PropertyRef("original_name")  # Original package name from SBOM
    version: PropertyRef = PropertyRef("version")  # Resolved version
    requirements: PropertyRef = PropertyRef("requirements")  # Version constraint from manifest
    ecosystem: PropertyRef = PropertyRef("ecosystem")  # Normalized ecosystem (e.g., pypi, npm)
    package_manager: PropertyRef = PropertyRef(
        "package_manager"
    )  # npm, pypi, golang, maven, etc.
    manifest_file: PropertyRef = PropertyRef("manifest_file")  # Manifest filename
    purl: PropertyRef = PropertyRef("purl")  # Package URL (e.g., pkg:pypi/requests@2.31.0)
    type: PropertyRef = PropertyRef("type")  # Package type from PURL
    normalized_id: PropertyRef = PropertyRef("normalized_id", extra_index=True)  # Cross-tool matching ID
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabDependencyToProjectRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between Dependency and GitLabProject.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabDependencyToProjectRel(CartographyRelSchema):
    """
    Sub-resource relationship from Dependency to GitLabProject.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_url", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabDependencyToProjectRelProperties = (
        GitLabDependencyToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabProjectRequiresDependencyRelProperties(CartographyRelProperties):
    """
    Properties for the REQUIRES relationship between GitLabProject and Dependency.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectRequiresDependencyRel(CartographyRelSchema):
    """
    Relationship from GitLabProject to Dependency.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_url", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REQUIRES"
    properties: GitLabProjectRequiresDependencyRelProperties = (
        GitLabProjectRequiresDependencyRelProperties()
    )


@dataclass(frozen=True)
class GitLabDependencyFileHasDependencyRelProperties(CartographyRelProperties):
    """
    Properties for the HAS_DEP relationship between GitLabDependencyFile and Dependency.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabDependencyFileHasDependencyRel(CartographyRelSchema):
    """
    Relationship from GitLabDependencyFile to Dependency.
    This relationship is optional - only created when manifest_id is present.
    """

    target_node_label: str = "GitLabDependencyFile"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("manifest_id")}  # Get from node data, not kwargs
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEP"
    properties: GitLabDependencyFileHasDependencyRelProperties = (
        GitLabDependencyFileHasDependencyRelProperties()
    )


@dataclass(frozen=True)
class GitLabDependencySchema(CartographyNodeSchema):
    """
    Schema for GitLab Dependency nodes.
    """

    label: str = "GitLabDependency"
    properties: GitLabDependencyNodeProperties = GitLabDependencyNodeProperties()
    sub_resource_relationship: GitLabDependencyToProjectRel = (
        GitLabDependencyToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabProjectRequiresDependencyRel(),  # Project requires dependency
            GitLabDependencyFileHasDependencyRel(),  # Dependency file has dependency
        ]
    )
