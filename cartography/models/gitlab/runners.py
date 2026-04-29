"""
GitLab Runner Schema

Runners execute CI/CD jobs in GitLab. They exist at three scopes:
- instance_type: shared across the whole GitLab instance (org-scoped here)
- group_type: scoped to a group and its descendants
- project_type: scoped to a single project

We model all three with the same Neo4j label `GitLabRunner`, but with three
distinct schemas so each scope's cleanup is correctly bounded to its parent.
"""

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
class GitLabRunnerNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Runner node.

    `run_untagged`, `locked`, and `access_level` are security-relevant: an
    untagged runner with `access_level=not_protected` will execute jobs from
    any project that can reach it, including from non-protected branches.
    """

    id: PropertyRef = PropertyRef("id")  # Numeric GitLab runner ID
    description: PropertyRef = PropertyRef("description")
    runner_type: PropertyRef = PropertyRef("runner_type", extra_index=True)
    is_shared: PropertyRef = PropertyRef("is_shared")
    active: PropertyRef = PropertyRef("active")
    paused: PropertyRef = PropertyRef("paused")
    online: PropertyRef = PropertyRef("online")
    status: PropertyRef = PropertyRef("status", extra_index=True)
    ip_address: PropertyRef = PropertyRef("ip_address")
    architecture: PropertyRef = PropertyRef("architecture")
    platform: PropertyRef = PropertyRef("platform")
    contacted_at: PropertyRef = PropertyRef("contacted_at")
    tag_list: PropertyRef = PropertyRef("tag_list")
    run_untagged: PropertyRef = PropertyRef("run_untagged")
    locked: PropertyRef = PropertyRef("locked")
    access_level: PropertyRef = PropertyRef("access_level")
    maximum_timeout: PropertyRef = PropertyRef("maximum_timeout")
    gitlab_url: PropertyRef = PropertyRef("gitlab_url", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# =============================================================================
# Instance-level Runner (sub-resource = GitLabOrganization)
# =============================================================================


@dataclass(frozen=True)
class GitLabInstanceRunnerToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabInstanceRunnerToOrganizationRel(CartographyRelSchema):
    """Sub-resource for instance-level runners — scoped to GitLabOrganization."""

    target_node_label: str = "GitLabOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("org_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabInstanceRunnerToOrganizationRelProperties = (
        GitLabInstanceRunnerToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitLabInstanceRunnerSchema(CartographyNodeSchema):
    """Schema for instance-level GitLab runners."""

    label: str = "GitLabRunner"
    properties: GitLabRunnerNodeProperties = GitLabRunnerNodeProperties()
    sub_resource_relationship: GitLabInstanceRunnerToOrganizationRel = (
        GitLabInstanceRunnerToOrganizationRel()
    )


# =============================================================================
# Group-level Runner (sub-resource = GitLabGroup)
# =============================================================================


@dataclass(frozen=True)
class GitLabGroupRunnerToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabGroupRunnerToGroupRel(CartographyRelSchema):
    """Sub-resource for group-level runners — scoped to GitLabGroup."""

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("group_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabGroupRunnerToGroupRelProperties = (
        GitLabGroupRunnerToGroupRelProperties()
    )


@dataclass(frozen=True)
class GitLabGroupRunnerSchema(CartographyNodeSchema):
    """Schema for group-level GitLab runners."""

    label: str = "GitLabRunner"
    properties: GitLabRunnerNodeProperties = GitLabRunnerNodeProperties()
    sub_resource_relationship: GitLabGroupRunnerToGroupRel = (
        GitLabGroupRunnerToGroupRel()
    )


# =============================================================================
# Project-level Runner (sub-resource = GitLabProject)
# =============================================================================


@dataclass(frozen=True)
class GitLabProjectRunnerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectRunnerToProjectRel(CartographyRelSchema):
    """Sub-resource for project-level runners — scoped to GitLabProject."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabProjectRunnerToProjectRelProperties = (
        GitLabProjectRunnerToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabProjectRunnerSchema(CartographyNodeSchema):
    """Schema for project-level GitLab runners."""

    label: str = "GitLabRunner"
    properties: GitLabRunnerNodeProperties = GitLabRunnerNodeProperties()
    sub_resource_relationship: GitLabProjectRunnerToProjectRel = (
        GitLabProjectRunnerToProjectRel()
    )
