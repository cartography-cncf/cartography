"""
GitLab Terraform State Schema

Models GitLab-managed Terraform HTTP backend states stored per project.
Each state is scoped to a GitLabProject (sub-resource relationship).
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
class GitLabTerraformStateNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLabTerraformState node.

    Represents a single Terraform state managed by GitLab's HTTP backend.
    The composite id is "<project_id>/<name>" for global uniqueness.
    """

    id: PropertyRef = PropertyRef("id")  # "<project_id>/<name>"
    name: PropertyRef = PropertyRef("name", extra_index=True)  # State name
    project_id: PropertyRef = PropertyRef("project_id", extra_index=True)
    locked: PropertyRef = PropertyRef("locked")  # bool
    locked_at: PropertyRef = PropertyRef("locked_at")
    locked_by_user_id: PropertyRef = PropertyRef("locked_by_user_id")
    updated_at: PropertyRef = PropertyRef("updated_at")
    latest_version_serial: PropertyRef = PropertyRef("latest_version_serial")
    latest_version_created_at: PropertyRef = PropertyRef("latest_version_created_at")
    latest_version_created_by_user_id: PropertyRef = PropertyRef(
        "latest_version_created_by_user_id"
    )
    latest_version_job_id: PropertyRef = PropertyRef("latest_version_job_id")
    latest_version_pipeline_id: PropertyRef = PropertyRef("latest_version_pipeline_id")
    gitlab_url: PropertyRef = PropertyRef("gitlab_url", extra_index=True)
    state_url: PropertyRef = PropertyRef("state_url")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabTerraformStateToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabTerraformStateToProjectRel(CartographyRelSchema):
    """
    Sub-resource relationship: GitLabTerraformState is scoped to a GitLabProject.
    (:GitLabProject)-[:HAS_TERRAFORM_STATE]->(:GitLabTerraformState)
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TERRAFORM_STATE"
    properties: GitLabTerraformStateToProjectRelProperties = (
        GitLabTerraformStateToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabTerraformStateSchema(CartographyNodeSchema):
    """
    Schema for GitLabTerraformState nodes.

    Terraform states are project-scoped. The sub_resource_relationship points to the
    owning GitLabProject so cleanup removes stale states when a project is re-synced.
    """

    label: str = "GitLabTerraformState"
    properties: GitLabTerraformStateNodeProperties = (
        GitLabTerraformStateNodeProperties()
    )
    sub_resource_relationship: GitLabTerraformStateToProjectRel = (
        GitLabTerraformStateToProjectRel()
    )
