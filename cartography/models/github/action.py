"""
GitHub Action schema definition.

Represents third-party GitHub Actions used in workflows.
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
class GitHubActionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    version: PropertyRef = PropertyRef("version")
    is_pinned: PropertyRef = PropertyRef("is_pinned")
    is_local: PropertyRef = PropertyRef("is_local")
    full_name: PropertyRef = PropertyRef("full_name")


@dataclass(frozen=True)
class GitHubActionToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from action to organization.

    This uses org as the sub-resource so that cleanup is scoped to the organization.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubActionToOrgRelProperties = GitHubActionToOrgRelProperties()


@dataclass(frozen=True)
class GitHubActionToWorkflowRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubActionToWorkflowRel(CartographyRelSchema):
    """Relationship from action to the workflow that uses it."""

    target_node_label: str = "GitHubWorkflow"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workflow_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES_ACTION"
    properties: GitHubActionToWorkflowRelProperties = (
        GitHubActionToWorkflowRelProperties()
    )


@dataclass(frozen=True)
class GitHubActionSchema(CartographyNodeSchema):
    """
    Schema for GitHub Actions used in workflows.

    Uses GitHubOrganization as the sub-resource for cleanup scoping.
    The relationship to GitHubWorkflow is in other_relationships.
    """

    label: str = "GitHubAction"
    properties: GitHubActionNodeProperties = GitHubActionNodeProperties()
    sub_resource_relationship: GitHubActionToOrgRel = GitHubActionToOrgRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubActionToWorkflowRel()],
    )
