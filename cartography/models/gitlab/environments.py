"""
GitLab Environment Schema

Environments are GitLab's deployment targets (production, staging, ...). Each
project has its own set of environments. The composite `id` includes the
project_id because GitLab's environment IDs are unique per-project, not
globally.

The environment carries an ``HAS_CI_VARIABLE`` relationship to every
project-level CI variable that applies to it (exact-name match on
``environment_scope`` or wildcard ``*``). The link is modelled as a standard
relationship with a ``one_to_many=True`` matcher, not a MatchLink — the
endpoints share the same sub-resource (the project), so the framework's
default cleanup tied to the environment node is sufficient and there is no
need for a separate MatchLink load + cleanup.
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
class GitLabEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Composite identifier formed from the project ID and GitLab environment ID.",
    )
    gitlab_id: PropertyRef = PropertyRef(
        "gitlab_id",
        description="Numeric GitLab environment ID, unique within its project.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Deployment environment name.",
    )
    slug: PropertyRef = PropertyRef(
        "slug",
        description="URL-safe deployment environment slug.",
    )
    external_url: PropertyRef = PropertyRef(
        "external_url",
        description="URL where the deployment environment is reachable.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Deployment environment state: available or stopped.",
    )
    tier: PropertyRef = PropertyRef(
        "tier",
        description="Deployment tier: production, staging, testing, development, or other.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when GitLab created the environment.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when GitLab last updated the environment.",
    )
    auto_stop_at: PropertyRef = PropertyRef(
        "auto_stop_at",
        description="Timestamp when GitLab is scheduled to stop the environment automatically.",
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
# Environment <-> Project (sub-resource and HAS_ENVIRONMENT)
# =============================================================================


@dataclass(frozen=True)
class GitLabProjectHasEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectHasEnvironmentRel(CartographyRelSchema):
    """A GitLab project contains a deployment environment."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id"),
            "gitlab_url": PropertyRef("gitlab_url"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ENVIRONMENT"
    properties: GitLabProjectHasEnvironmentRelProperties = (
        GitLabProjectHasEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class GitLabEnvironmentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabEnvironmentToProjectRel(CartographyRelSchema):
    """A GitLab project owns the environment as a sub-resource."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabEnvironmentToProjectRelProperties = (
        GitLabEnvironmentToProjectRelProperties()
    )


# =============================================================================
# Environment -> CI Variable (one_to_many, applied at env load time)
# =============================================================================


@dataclass(frozen=True)
class GitLabEnvironmentToCIVariableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabEnvironmentToCIVariableRel(CartographyRelSchema):
    """An environment uses each project CI variable whose scope applies to it."""

    target_node_label: str = "GitLabCIVariable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("linked_variable_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_CI_VARIABLE"
    properties: GitLabEnvironmentToCIVariableRelProperties = (
        GitLabEnvironmentToCIVariableRelProperties()
    )


@dataclass(frozen=True)
class GitLabEnvironmentSchema(CartographyNodeSchema):
    """A deployment environment defined within a GitLab project."""

    label: str = "GitLabEnvironment"
    properties: GitLabEnvironmentNodeProperties = GitLabEnvironmentNodeProperties()
    sub_resource_relationship: GitLabEnvironmentToProjectRel = (
        GitLabEnvironmentToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabProjectHasEnvironmentRel(),
            GitLabEnvironmentToCIVariableRel(),
        ],
    )
