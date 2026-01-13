"""
GitLab Organization Schema

In GitLab, organizations are top-level groups (where parent_id is null).
They serve as the root of the organizational hierarchy and contain groups and projects.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class GitLabOrganizationNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Organization node.

    Organizations are top-level groups in GitLab's hierarchy.
    """

    id: PropertyRef = PropertyRef("web_url")  # Unique identifier
    name: PropertyRef = PropertyRef("name", extra_index=True)  # Display name
    path: PropertyRef = PropertyRef("path", extra_index=True)  # URL path slug
    full_path: PropertyRef = PropertyRef(
        "full_path", extra_index=True
    )  # Full hierarchy path
    description: PropertyRef = PropertyRef("description")
    visibility: PropertyRef = PropertyRef("visibility")  # private, internal, public
    created_at: PropertyRef = PropertyRef("created_at")
    gitlab_url: PropertyRef = PropertyRef(
        "gitlab_url"
    )  # GitLab instance URL for scoped cleanup
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabOrganizationSchema(CartographyNodeSchema):
    """
    Schema for GitLab Organization nodes.

    Organizations are top-level groups (parent_id is null) that serve as the root
    of GitLab's organizational hierarchy. They are top-level resources with no parent,
    so they have no sub_resource_relationship.
    """

    label: str = "GitLabOrganization"
    properties: GitLabOrganizationNodeProperties = GitLabOrganizationNodeProperties()
    # No sub_resource_relationship - organizations are top-level resources
