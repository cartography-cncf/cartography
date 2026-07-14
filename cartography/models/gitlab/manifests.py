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

    id: PropertyRef = PropertyRef(
        "id",
        description="Unique identifier formed from the project URL and file path.",
    )
    path: PropertyRef = PropertyRef(
        "path",
        description="Path to the dependency file in the repository.",
    )
    filename: PropertyRef = PropertyRef(
        "filename",
        extra_index=True,
        description="Dependency file name.",
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="Numeric ID of the parent GitLab project.",
    )
    project_url: PropertyRef = PropertyRef(
        "project_url",
        description="URL of the parent GitLab project.",
    )
    gitlab_url: PropertyRef = PropertyRef(
        "gitlab_url",
        extra_index=True,
        description="URL of the GitLab instance.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


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
        {
            "id": PropertyRef("project_id"),
            "gitlab_url": PropertyRef("gitlab_url"),
        },
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
        {
            "id": PropertyRef("project_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabDependencyFileToProjectRelProperties = (
        GitLabDependencyFileToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabDependencyFileSchema(CartographyNodeSchema):
    """A dependency manifest file found in a GitLab project."""

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
