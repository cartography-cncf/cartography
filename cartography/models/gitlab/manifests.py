"""
GitLab Dependency File Schema

Represents dependency manifest files in GitLab projects.
These files declare project dependencies (e.g., package.json, requirements.txt, Gemfile, etc.).
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
class GitLabDependencyFileNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Dependency File node.

    Represents manifest files that declare dependencies.
    """

    id: PropertyRef = PropertyRef("id")  # Unique identifier
    path: PropertyRef = PropertyRef(
        "path"
    )  # Path to file in repository (e.g., "src/package.json")
    filename: PropertyRef = PropertyRef(
        "filename", extra_index=True
    )  # File name (e.g., "package.json")
    project_url: PropertyRef = PropertyRef("project_url")  # Parent project URL
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectHasDependencyFileRelProperties(CartographyRelProperties):
    """
    Properties for the HAS_DEPENDENCY_FILE relationship between GitLabProject and GitLabDependencyFile.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectHasDependencyFileRel(CartographyRelSchema):
    """
    Relationship from GitLabProject to GitLabDependencyFile.
    Created when dependency files are loaded to establish the project-file connection.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_url")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DEPENDENCY_FILE"
    properties: GitLabProjectHasDependencyFileRelProperties = (
        GitLabProjectHasDependencyFileRelProperties()
    )


@dataclass(frozen=True)
class GitLabDependencyFileToProjectRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between GitLabDependencyFile and GitLabProject.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabDependencyFileToProjectRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabDependencyFile to GitLabProject.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_url", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabDependencyFileToProjectRelProperties = (
        GitLabDependencyFileToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabDependencyFileSchema(CartographyNodeSchema):
    """
    Schema for GitLab Dependency File nodes.

    Dependency files belong to projects and have two relationships:
    - RESOURCE: Sub-resource relationship for cleanup scoping (DependencyFile -> Project)
    - HAS_DEPENDENCY_FILE: Semantic relationship showing project ownership (Project -> DependencyFile)
    """

    label: str = "GitLabDependencyFile"
    properties: GitLabDependencyFileNodeProperties = (
        GitLabDependencyFileNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabProjectHasDependencyFileRel(),  # Project has this dependency file
        ],
    )
    sub_resource_relationship: GitLabDependencyFileToProjectRel = (
        GitLabDependencyFileToProjectRel()
    )
