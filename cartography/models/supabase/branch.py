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
class SupabaseBranchNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The branch id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the branch"
    )
    # A preview branch is itself a full project, so project_ref points at the
    # ephemeral project holding the branch's data.
    project_ref: PropertyRef = PropertyRef(
        "project_ref",
        extra_index=True,
        description="Ref of the ephemeral project holding the branch's data",
    )
    parent_project_ref: PropertyRef = PropertyRef(
        "parent_project_ref",
        description="Ref of the project the branch was created from",
    )
    is_default: PropertyRef = PropertyRef(
        "is_default", description="Whether this is the project's default branch"
    )
    persistent: PropertyRef = PropertyRef(
        "persistent",
        description="Whether the branch survives after its pull request closes",
    )
    with_data: PropertyRef = PropertyRef(
        "with_data", description="Whether the branch was seeded with production data"
    )
    status: PropertyRef = PropertyRef("status", description="Status of the branch")
    preview_project_status: PropertyRef = PropertyRef(
        "preview_project_status", description="Status of the branch's preview project"
    )
    git_branch: PropertyRef = PropertyRef(
        "git_branch", description="The Git branch this preview tracks"
    )
    pr_number: PropertyRef = PropertyRef(
        "pr_number", description="The pull request number this preview tracks"
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the branch was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the branch was last changed"
    )
    review_requested_at: PropertyRef = PropertyRef(
        "review_requested_at", description="When review was requested"
    )
    deletion_scheduled_at: PropertyRef = PropertyRef(
        "deletion_scheduled_at", description="When the branch is scheduled for deletion"
    )


@dataclass(frozen=True)
class SupabaseBranchToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseBranch)
class SupabaseBranchToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseBranchToProjectRelProperties = (
        SupabaseBranchToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseBranchOfProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseBranch)-[:BRANCH_OF]->(:SupabaseProject)
class SupabaseBranchOfProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_project_ref")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BRANCH_OF"
    properties: SupabaseBranchOfProjectRelProperties = (
        SupabaseBranchOfProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseBranchSchema(CartographyNodeSchema):
    """Represents a database preview branch. Branching is a paid feature tied to the GitHub integration; on projects without it this node type is simply absent."""

    label: str = "SupabaseBranch"
    properties: SupabaseBranchNodeProperties = SupabaseBranchNodeProperties()
    sub_resource_relationship: SupabaseBranchToProjectRel = SupabaseBranchToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SupabaseBranchOfProjectRel(),
        ],
    )
