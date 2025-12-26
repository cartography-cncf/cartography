"""
GitLab Project Schema

In GitLab, projects are repositories/codebases that belong to groups.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitLabProjectNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Project node.

    Projects are GitLab's equivalent of repositories.
    """

    id: PropertyRef = PropertyRef("web_url")  # Unique identifier
    name: PropertyRef = PropertyRef("name", extra_index=True)  # Project name
    path: PropertyRef = PropertyRef("path", extra_index=True)  # URL path slug
    path_with_namespace: PropertyRef = PropertyRef(
        "path_with_namespace", extra_index=True
    )  # Full path
    description: PropertyRef = PropertyRef("description")
    visibility: PropertyRef = PropertyRef("visibility")  # private, internal, public
    default_branch: PropertyRef = PropertyRef("default_branch")  # Default branch name
    archived: PropertyRef = PropertyRef("archived")  # Is project archived
    created_at: PropertyRef = PropertyRef("created_at")
    last_activity_at: PropertyRef = PropertyRef("last_activity_at")
    languages: PropertyRef = PropertyRef(
        "languages", extra_index=True
    )  # JSON dict of language name -> percentage
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabGroupCanAccessProjectRelProperties(CartographyRelProperties):
    """
    Properties for the CAN_ACCESS relationship between GitLabGroup and GitLabProject.

    This represents group sharing in GitLab, where a group is given access to a project.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    access_level: PropertyRef = PropertyRef("access_level")  # 50, 40, 30, 20, 10


@dataclass(frozen=True)
class GitLabGroupCanAccessProjectRel(CartographyRelSchema):
    """
    Relationship from GitLabGroup to GitLabProject representing group access.
    """

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_url")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_ACCESS"
    properties: GitLabGroupCanAccessProjectRelProperties = (
        GitLabGroupCanAccessProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabProjectToGroupRelProperties(CartographyRelProperties):
    """
    Properties for the MEMBER_OF relationship between GitLabProject and GitLabGroup.
    Represents the immediate parent group of a project (for projects in nested groups).
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectToGroupRel(CartographyRelSchema):
    """
    Relationship from GitLabProject to GitLabGroup via MEMBER_OF.
    Represents the immediate parent group of a project (for projects in nested groups).
    """

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: GitLabProjectToGroupRelProperties = GitLabProjectToGroupRelProperties()


@dataclass(frozen=True)
class GitLabProjectToOrganizationRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between GitLabProject and GitLabOrganization.
    Used for cleanup scoping - all projects belong to an organization.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectToOrganizationRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabProject to GitLabOrganization.
    All projects belong to an organization, used for cleanup scoping.
    Projects are cleaned up per organization.
    """

    target_node_label: str = "GitLabOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabProjectToOrganizationRelProperties = (
        GitLabProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitLabProjectSchema(CartographyNodeSchema):
    """
    Schema for GitLab Project nodes.

    Projects are repositories/codebases that belong to an organization.
    They may also have a RESOURCE relationship to a GitLabGroup (for projects in nested groups).
    They can have group access permissions, branches, and dependency files.
    """

    label: str = "GitLabProject"
    properties: GitLabProjectNodeProperties = GitLabProjectNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabGroupCanAccessProjectRel(),  # Group has access to project (sharing)
            GitLabProjectToGroupRel(),  # Project belongs to group (for projects in nested groups)
        ],
    )
    sub_resource_relationship: GitLabProjectToOrganizationRel = (
        GitLabProjectToOrganizationRel()
    )
    # Add GitLabRepository label for backwards compatibility
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GitLabRepository"])
