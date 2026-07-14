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

    id: PropertyRef = PropertyRef(
        "id",
        description="Numeric GitLab ID of the top-level group.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Display name of the organization.",
    )
    path: PropertyRef = PropertyRef(
        "path",
        extra_index=True,
        description="URL path slug of the organization.",
    )
    full_path: PropertyRef = PropertyRef(
        "full_path",
        extra_index=True,
        description="Full path of the top-level group.",
    )
    web_url: PropertyRef = PropertyRef(
        "web_url",
        extra_index=True,
        description="URL for viewing the organization in GitLab.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Human-readable description of the organization.",
    )
    visibility: PropertyRef = PropertyRef(
        "visibility",
        description="Organization visibility: private, internal, or public.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when GitLab created the top-level group.",
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
class GitLabOrganizationSchema(CartographyNodeSchema):
    """A configured GitLab top-level group that scopes an organization sync."""

    label: str = "GitLabOrganization"
    properties: GitLabOrganizationNodeProperties = GitLabOrganizationNodeProperties()
    # No sub_resource_relationship - organizations are top-level resources
