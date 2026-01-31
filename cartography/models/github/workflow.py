"""
GitHub Workflow schema definition.

Represents GitHub Actions workflow definition files in repositories.
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
class GitHubWorkflowNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    path: PropertyRef = PropertyRef("path")
    state: PropertyRef = PropertyRef("state")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    html_url: PropertyRef = PropertyRef("html_url")


@dataclass(frozen=True)
class GitHubWorkflowToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubWorkflowToRepoRel(CartographyRelSchema):
    """Relationship from workflow to its repository."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_WORKFLOW"
    properties: GitHubWorkflowToRepoRelProperties = GitHubWorkflowToRepoRelProperties()


@dataclass(frozen=True)
class GitHubWorkflowToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubWorkflowToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from workflow to organization.

    This uses org as the sub-resource so that cleanup is scoped to the organization.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubWorkflowToOrgRelProperties = GitHubWorkflowToOrgRelProperties()


@dataclass(frozen=True)
class GitHubWorkflowSchema(CartographyNodeSchema):
    """
    Schema for GitHub Actions workflows.

    Uses GitHubOrganization as the sub-resource for cleanup scoping.
    The relationship to GitHubRepository is in other_relationships.
    """

    label: str = "GitHubWorkflow"
    properties: GitHubWorkflowNodeProperties = GitHubWorkflowNodeProperties()
    sub_resource_relationship: GitHubWorkflowToOrgRel = GitHubWorkflowToOrgRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubWorkflowToRepoRel()],
    )
