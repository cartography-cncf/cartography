"""
GitLab Branch Schema

Represents Git branches in GitLab projects.
Branches belong to projects via RESOURCE relationship (cleanup chain).
Projects also have a semantic HAS_BRANCH relationship to branches (defined in projects.py).
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
class GitLabBranchNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Branch node.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Unique branch identifier formed from the project URL and branch name.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Branch name.",
    )
    protected: PropertyRef = PropertyRef(
        "protected",
        description="Whether the branch is protected.",
    )
    default: PropertyRef = PropertyRef(
        "default",
        description="Whether this is the project's default branch.",
    )
    web_url: PropertyRef = PropertyRef(
        "web_url",
        description="URL for viewing the branch in GitLab.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GitLabProjectHasBranchRelProperties(CartographyRelProperties):
    """
    Properties for the HAS_BRANCH relationship between GitLabProject and GitLabBranch.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectHasBranchRel(CartographyRelSchema):
    """
    Relationship from GitLabProject to GitLabBranch.
    Created when branches are loaded to establish the project-branch connection.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id"),
            "gitlab_url": PropertyRef("gitlab_url"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_BRANCH"
    properties: GitLabProjectHasBranchRelProperties = (
        GitLabProjectHasBranchRelProperties()
    )


@dataclass(frozen=True)
class GitLabBranchToProjectRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between GitLabBranch and GitLabProject.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabBranchToProjectRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabBranch to GitLabProject.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabBranchToProjectRelProperties = (
        GitLabBranchToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabBranchSchema(CartographyNodeSchema):
    """
    Schema for GitLab Branch nodes.

    Branches belong to projects and have two relationships:
    - RESOURCE: Sub-resource relationship for cleanup scoping (Branch -> Project)
    - HAS_BRANCH: Semantic relationship showing project ownership (Project -> Branch)
    """

    label: str = "GitLabBranch"
    properties: GitLabBranchNodeProperties = GitLabBranchNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabProjectHasBranchRel(),  # Project has this branch
        ],
    )
    sub_resource_relationship: GitLabBranchToProjectRel = GitLabBranchToProjectRel()
