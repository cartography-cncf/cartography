"""
GitLab Environment Schema

Environments are GitLab's deployment targets (production, staging, ...). Each
project has its own set of environments. The composite `id` includes the
project_id because GitLab's environment IDs are unique per-project, not
globally.

This module also defines a scoped MatchLink that connects environments to
their CI/CD variables. The MatchLink is scoped to the parent GitLabProject so
the cardinality of the lookup is bounded to the project, not the whole graph.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitLabEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")  # Composite: f"{project_id}:{gitlab_env_id}"
    gitlab_id: PropertyRef = PropertyRef("gitlab_id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    slug: PropertyRef = PropertyRef("slug")
    external_url: PropertyRef = PropertyRef("external_url")
    state: PropertyRef = PropertyRef("state")
    tier: PropertyRef = PropertyRef("tier")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    auto_stop_at: PropertyRef = PropertyRef("auto_stop_at")
    gitlab_url: PropertyRef = PropertyRef("gitlab_url", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# =============================================================================
# Environment <-> Project (sub-resource and HAS_ENVIRONMENT)
# =============================================================================


@dataclass(frozen=True)
class GitLabProjectHasEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectHasEnvironmentRel(CartographyRelSchema):
    """`(:GitLabProject)-[:HAS_ENVIRONMENT]->(:GitLabEnvironment)`."""

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
    """Sub-resource relationship — scoped to GitLabProject."""

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


@dataclass(frozen=True)
class GitLabEnvironmentSchema(CartographyNodeSchema):
    label: str = "GitLabEnvironment"
    properties: GitLabEnvironmentNodeProperties = GitLabEnvironmentNodeProperties()
    sub_resource_relationship: GitLabEnvironmentToProjectRel = (
        GitLabEnvironmentToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitLabProjectHasEnvironmentRel()],
    )


# =============================================================================
# Environment -> CI Variable MatchLink (project-scoped)
# =============================================================================


@dataclass(frozen=True)
class GitLabEnvironmentToCIVariableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id", set_in_kwargs=True
    )


@dataclass(frozen=True)
class GitLabEnvironmentToCIVariableMatchLink(CartographyRelSchema):
    """
    `(:GitLabEnvironment)-[:HAS_CI_VARIABLE]->(:GitLabCIVariable)`

    A variable is linked to an environment when its `environment_scope` is
    either an exact match for the environment's name, or the wildcard `*`.
    The link is scoped via `MatchLinkSubResource` to the parent GitLabProject
    so the lookup is bounded.
    """

    source_node_label: str = "GitLabEnvironment"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("env_id")},
    )
    target_node_label: str = "GitLabCIVariable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("variable_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_CI_VARIABLE"
    properties: GitLabEnvironmentToCIVariableRelProperties = (
        GitLabEnvironmentToCIVariableRelProperties()
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="GitLabProject",
        target_node_matcher=make_target_node_matcher(
            {
                "id": PropertyRef("_sub_resource_id", set_in_kwargs=True),
                "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
            },
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="GitLabProject",
        target_node_matcher=make_target_node_matcher(
            {
                "id": PropertyRef("_sub_resource_id", set_in_kwargs=True),
                "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
            },
        ),
        direction=LinkDirection.INWARD,
        rel_label="HAS_CI_VARIABLE",
    )
