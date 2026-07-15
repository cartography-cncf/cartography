"""
GitHub Workflow schema definition.

Represents GitHub Actions workflow definition files in repositories.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubWorkflowNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="GitHub workflow ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Workflow name."
    )
    path: PropertyRef = PropertyRef(
        "path", extra_index=True, description="Repository-relative workflow file path."
    )
    state: PropertyRef = PropertyRef(
        "state",
        description=(
            "Workflow state, such as `active`, `disabled_manually`, or "
            "`disabled_inactivity`."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the resource was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the resource was last updated."
    )
    repo_url: PropertyRef = PropertyRef(
        "repo_url", extra_index=True, description="URL of the containing repository."
    )
    # Parsed fields from workflow YAML
    trigger_events: PropertyRef = PropertyRef(
        "trigger_events", description="Trigger event names parsed from workflow YAML."
    )
    permissions_actions: PropertyRef = PropertyRef(
        "permissions_actions",
        description="Actions permission level parsed from workflow YAML.",
    )
    permissions_contents: PropertyRef = PropertyRef(
        "permissions_contents",
        description="Contents permission level parsed from workflow YAML.",
    )
    permissions_packages: PropertyRef = PropertyRef(
        "permissions_packages",
        description="Packages permission level parsed from workflow YAML.",
    )
    permissions_pull_requests: PropertyRef = PropertyRef(
        "permissions_pull_requests",
        description="Pull requests permission level parsed from workflow YAML.",
    )
    permissions_issues: PropertyRef = PropertyRef(
        "permissions_issues",
        description="Issues permission level parsed from workflow YAML.",
    )
    permissions_deployments: PropertyRef = PropertyRef(
        "permissions_deployments",
        description="Deployments permission level parsed from workflow YAML.",
    )
    permissions_statuses: PropertyRef = PropertyRef(
        "permissions_statuses",
        description="Statuses permission level parsed from workflow YAML.",
    )
    permissions_checks: PropertyRef = PropertyRef(
        "permissions_checks",
        description="Checks permission level parsed from workflow YAML.",
    )
    permissions_id_token: PropertyRef = PropertyRef(
        "permissions_id_token",
        description="ID token permission level parsed from workflow YAML.",
    )
    permissions_security_events: PropertyRef = PropertyRef(
        "permissions_security_events",
        description="Security events permission level parsed from workflow YAML.",
    )
    env_vars: PropertyRef = PropertyRef(
        "env_vars",
        description="Top-level environment variable names parsed from workflow YAML.",
    )
    job_count: PropertyRef = PropertyRef(
        "job_count", description="Number of jobs parsed from workflow YAML."
    )
    has_reusable_workflow_calls: PropertyRef = PropertyRef(
        "has_reusable_workflow_calls",
        description="Whether parsed workflow YAML calls a reusable workflow.",
    )


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
class GitHubWorkflowToSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubWorkflowToSecretRel(CartographyRelSchema):
    """
    Relationship from workflow to secrets it references.

    Uses one_to_many to support workflows that reference multiple secrets.
    The secret_ids field should contain a list of GitHubActionsSecret IDs.
    """

    target_node_label: str = "GitHubActionsSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("secret_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES_SECRET"
    properties: GitHubWorkflowToSecretRelProperties = (
        GitHubWorkflowToSecretRelProperties()
    )


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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CICDPipeline"])
    sub_resource_relationship: GitHubWorkflowToOrgRel = GitHubWorkflowToOrgRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubWorkflowToRepoRel(),
            GitHubWorkflowToSecretRel(),
        ],
    )
