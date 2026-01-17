"""
GitLab Group Schema

In GitLab, groups can be nested within other groups and belong to a top-level organization.
Groups serve a similar purpose to GitHub Teams, providing a way to organize users and projects.
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
class GitLabGroupNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Group node.

    Groups are nested within a GitLab organization and can contain other groups and projects.
    """

    id: PropertyRef = PropertyRef("web_url")  # Unique identifier
    name: PropertyRef = PropertyRef("name", extra_index=True)  # Display name
    path: PropertyRef = PropertyRef("path", extra_index=True)  # URL path slug
    full_path: PropertyRef = PropertyRef(
        "full_path", extra_index=True
    )  # Full hierarchy path
    description: PropertyRef = PropertyRef("description")
    visibility: PropertyRef = PropertyRef("visibility")  # private, internal, public
    parent_id: PropertyRef = PropertyRef(
        "parent_id"
    )  # ID of parent group (null if direct child of org)
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
        {"id": PropertyRef("parent_group_url")},
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
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabGroupToOrganizationRelProperties = (
        GitLabGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitLabGroupSchema(CartographyNodeSchema):
    """
    Schema for GitLab Group nodes.

    Groups are nested within a GitLab organization and can contain other groups and projects.
    Groups always have a RESOURCE relationship to their parent GitLabOrganization (used for cleanup scoping).
    Groups may have a MEMBER_OF relationship to a parent GitLabGroup (for nested hierarchies).
    """

    label: str = "GitLabGroup"
    properties: GitLabGroupNodeProperties = GitLabGroupNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabGroupToParentGroupRel(),  # Child group -> Parent group (nested hierarchy)
        ],
    )
    sub_resource_relationship: GitLabGroupToOrganizationRel = (
        GitLabGroupToOrganizationRel()
    )
