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

    id: PropertyRef = PropertyRef(
        "id",
        description="Numeric GitLab runner ID.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Human-readable runner description.",
    )
    runner_type: PropertyRef = PropertyRef(
        "runner_type",
        extra_index=True,
        description="Runner scope: instance_type, group_type, or project_type.",
    )
    is_shared: PropertyRef = PropertyRef(
        "is_shared",
        description="Whether the runner is shared across the GitLab instance.",
    )
    active: PropertyRef = PropertyRef(
        "active",
        description="Whether the runner is enabled.",
    )
    paused: PropertyRef = PropertyRef(
        "paused",
        description="Whether the runner is paused from accepting new jobs.",
    )
    online: PropertyRef = PropertyRef(
        "online",
        description="Whether the runner has contacted GitLab recently.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        extra_index=True,
        description="Current GitLab runner status.",
    )
    ip_address: PropertyRef = PropertyRef(
        "ip_address",
        description="Last known IP address of the runner.",
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description="CPU architecture reported by the runner.",
    )
    platform: PropertyRef = PropertyRef(
        "platform",
        description="Operating system platform reported by the runner.",
    )
    contacted_at: PropertyRef = PropertyRef(
        "contacted_at",
        description="Timestamp when the runner last contacted GitLab.",
    )
    tag_list: PropertyRef = PropertyRef(
        "tag_list",
        description="Tags used to route CI/CD jobs to the runner.",
    )
    run_untagged: PropertyRef = PropertyRef(
        "run_untagged",
        description="Whether the runner accepts jobs without matching tags.",
    )
    locked: PropertyRef = PropertyRef(
        "locked",
        description="Whether the runner is locked from assignment to additional projects.",
    )
    access_level: PropertyRef = PropertyRef(
        "access_level",
        description="Ref protection level required for jobs assigned to the runner.",
    )
    maximum_timeout: PropertyRef = PropertyRef(
        "maximum_timeout",
        description="Maximum job timeout enforced by the runner, in seconds.",
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
    """A GitLab CI/CD runner at instance, group, or project scope."""

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
    """A GitLab CI/CD runner at instance, group, or project scope."""

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
    """A GitLab CI/CD runner at instance, group, or project scope."""

    label: str = "GitLabRunner"
    properties: GitLabRunnerNodeProperties = GitLabRunnerNodeProperties()
    sub_resource_relationship: GitLabProjectRunnerToProjectRel = (
        GitLabProjectRunnerToProjectRel()
    )
