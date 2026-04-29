"""
GitLab CI/CD Variable Schema

GitLab CI/CD variables exist at two scopes:
- Group-level: shared across all projects in the group (and descendants)
- Project-level: scoped to a single project

GitLab does not distinguish "secrets" from "variables" at the API level —
the `masked`, `masked_and_hidden`, and `protected` flags carry the security
metadata. The variable's `value` is intentionally NOT ingested: only the
metadata is stored.

The composite `id` uses {scope_type}:{scope_id}:{key}:{environment_scope}
because GitLab allows the same key to coexist with different
environment_scope values within the same scope.
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
class GitLabCIVariableNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab CI/CD variable node.

    `protected` and `masked` are the primary security signals: a variable
    that is `protected=False` can leak to a non-protected branch, and one
    that is `masked=False` can be echoed in build logs.
    """

    id: PropertyRef = PropertyRef("id")  # Composite: scope_type:scope_id:key:env_scope
    key: PropertyRef = PropertyRef("key", extra_index=True)
    variable_type: PropertyRef = PropertyRef("variable_type")
    protected: PropertyRef = PropertyRef("protected", extra_index=True)
    masked: PropertyRef = PropertyRef("masked")
    masked_and_hidden: PropertyRef = PropertyRef("masked_and_hidden")
    raw: PropertyRef = PropertyRef("raw")
    environment_scope: PropertyRef = PropertyRef("environment_scope", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    scope_type: PropertyRef = PropertyRef("scope_type")
    gitlab_url: PropertyRef = PropertyRef("gitlab_url", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# =============================================================================
# Group-level CI/CD variable
# =============================================================================


@dataclass(frozen=True)
class GitLabGroupCIVariableToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabGroupCIVariableToGroupRel(CartographyRelSchema):
    """Sub-resource for group-level CI variables — scoped to GitLabGroup."""

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("group_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabGroupCIVariableToGroupRelProperties = (
        GitLabGroupCIVariableToGroupRelProperties()
    )


@dataclass(frozen=True)
class GitLabGroupHasCIVariableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabGroupHasCIVariableRel(CartographyRelSchema):
    """`(:GitLabGroup)-[:HAS_CI_VARIABLE]->(:GitLabCIVariable)` — semantic edge."""

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("group_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CI_VARIABLE"
    properties: GitLabGroupHasCIVariableRelProperties = (
        GitLabGroupHasCIVariableRelProperties()
    )


@dataclass(frozen=True)
class GitLabGroupCIVariableSchema(CartographyNodeSchema):
    """Schema for group-level CI/CD variables.

    Two relationships to the parent group:
    - ``RESOURCE`` — used by the framework for cleanup scoping (convention).
    - ``HAS_CI_VARIABLE`` — semantic edge for graph queries.
    """

    label: str = "GitLabCIVariable"
    properties: GitLabCIVariableNodeProperties = GitLabCIVariableNodeProperties()
    sub_resource_relationship: GitLabGroupCIVariableToGroupRel = (
        GitLabGroupCIVariableToGroupRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitLabGroupHasCIVariableRel()],
    )


# =============================================================================
# Project-level CI/CD variable
# =============================================================================


@dataclass(frozen=True)
class GitLabProjectCIVariableToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectCIVariableToProjectRel(CartographyRelSchema):
    """Sub-resource for project-level CI variables — scoped to GitLabProject."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabProjectCIVariableToProjectRelProperties = (
        GitLabProjectCIVariableToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabProjectHasCIVariableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectHasCIVariableRel(CartographyRelSchema):
    """`(:GitLabProject)-[:HAS_CI_VARIABLE]->(:GitLabCIVariable)` — semantic edge."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CI_VARIABLE"
    properties: GitLabProjectHasCIVariableRelProperties = (
        GitLabProjectHasCIVariableRelProperties()
    )


@dataclass(frozen=True)
class GitLabProjectCIVariableSchema(CartographyNodeSchema):
    """Schema for project-level CI/CD variables.

    See :class:`GitLabGroupCIVariableSchema` for the rationale on why both
    ``RESOURCE`` and ``HAS_CI_VARIABLE`` edges exist.
    """

    label: str = "GitLabCIVariable"
    properties: GitLabCIVariableNodeProperties = GitLabCIVariableNodeProperties()
    sub_resource_relationship: GitLabProjectCIVariableToProjectRel = (
        GitLabProjectCIVariableToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitLabProjectHasCIVariableRel()],
    )
