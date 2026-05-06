"""
GitHub Actions self-hosted runner schema definitions.

GitHub exposes runners at both organization and repository scopes. A repository
may list runners inherited from the organization, so we model a single
``GitHubRunner`` node keyed by the runner's numeric id and attach scope-specific
relationships for cleanup and access semantics.
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
class GitHubRunnerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    os: PropertyRef = PropertyRef("os", extra_index=True)
    status: PropertyRef = PropertyRef("status", extra_index=True)
    busy: PropertyRef = PropertyRef("busy")
    ephemeral: PropertyRef = PropertyRef("ephemeral")
    labels: PropertyRef = PropertyRef("labels")
    label_types: PropertyRef = PropertyRef("label_types")


@dataclass(frozen=True)
class GitHubRunnerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubOrgRunnerToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubRunnerRelProperties = GitHubRunnerRelProperties()


@dataclass(frozen=True)
class GitHubOrgRunnerSchema(CartographyNodeSchema):
    label: str = "GitHubRunner"
    properties: GitHubRunnerNodeProperties = GitHubRunnerNodeProperties()
    sub_resource_relationship: GitHubOrgRunnerToOrganizationRel = (
        GitHubOrgRunnerToOrganizationRel()
    )


@dataclass(frozen=True)
class GitHubRepoRunnerToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "AVAILABLE_TO"
    properties: GitHubRunnerRelProperties = GitHubRunnerRelProperties()


@dataclass(frozen=True)
class GitHubRepoRunnerSchema(CartographyNodeSchema):
    label: str = "GitHubRunner"
    properties: GitHubRunnerNodeProperties = GitHubRunnerNodeProperties()
    sub_resource_relationship: GitHubRepoRunnerToRepositoryRel = (
        GitHubRepoRunnerToRepositoryRel()
    )
