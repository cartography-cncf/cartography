"""
GitLab Group Schema

In GitLab, groups can be nested within other groups and belong to a top-level organization.
Groups serve a similar purpose to GitHub Teams, providing a way to organize users and projects.
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
class GitLabGroupNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Group node.

    Groups are nested within a GitLab organization and can contain other groups and projects.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Numeric GitLab group ID.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Display name of the group.",
    )
    path: PropertyRef = PropertyRef(
        "path",
        extra_index=True,
        description="URL path slug of the group.",
    )
    full_path: PropertyRef = PropertyRef(
        "full_path",
        extra_index=True,
        description="Full group path including parent groups.",
    )
    web_url: PropertyRef = PropertyRef(
        "web_url",
        extra_index=True,
        description="URL for viewing the group in GitLab.",
    )
    gitlab_url: PropertyRef = PropertyRef(
        "gitlab_url",
        extra_index=True,
        description="URL of the GitLab instance.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Human-readable description of the group.",
    )
    visibility: PropertyRef = PropertyRef(
        "visibility",
        description="Group visibility: private, internal, or public.",
    )
    parent_id: PropertyRef = PropertyRef(
        "parent_id",
        description="Numeric ID of the immediate parent group.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when GitLab created the group.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GitLabGroupToParentGroupRelProperties(CartographyRelProperties):
    """
    Properties for the MEMBER_OF relationship between child and parent groups.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabGroupToParentGroupRel(CartographyRelSchema):
    """
    Relationship from a child GitLabGroup to its parent GitLabGroup.
    Used to represent the nested group hierarchy.
    """

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("parent_id"),
            "gitlab_url": PropertyRef("gitlab_url"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: GitLabGroupToParentGroupRelProperties = (
        GitLabGroupToParentGroupRelProperties()
    )


@dataclass(frozen=True)
class GitLabGroupToOrganizationRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between GitLabGroup and GitLabOrganization.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabGroupToOrganizationRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabGroup to GitLabOrganization.
    All groups belong to an organization, used for cleanup scoping.
    """

    target_node_label: str = "GitLabOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("org_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabGroupToOrganizationRelProperties = (
        GitLabGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitLabGroupSchema(CartographyNodeSchema):
    """A nested GitLab group within the configured top-level organization."""

    label: str = "GitLabGroup"
    properties: GitLabGroupNodeProperties = GitLabGroupNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabGroupToParentGroupRel(),  # Child group -> Parent group (nested hierarchy)
        ],
    )
    sub_resource_relationship: GitLabGroupToOrganizationRel = (
        GitLabGroupToOrganizationRel()
    )
