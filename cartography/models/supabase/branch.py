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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    # A preview branch is itself a full project, so project_ref points at the
    # ephemeral project holding the branch's data.
    project_ref: PropertyRef = PropertyRef("project_ref", extra_index=True)
    parent_project_ref: PropertyRef = PropertyRef("parent_project_ref")
    is_default: PropertyRef = PropertyRef("is_default")
    persistent: PropertyRef = PropertyRef("persistent")
    with_data: PropertyRef = PropertyRef("with_data")
    status: PropertyRef = PropertyRef("status")
    preview_project_status: PropertyRef = PropertyRef("preview_project_status")
    git_branch: PropertyRef = PropertyRef("git_branch")
    pr_number: PropertyRef = PropertyRef("pr_number")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    review_requested_at: PropertyRef = PropertyRef("review_requested_at")
    deletion_scheduled_at: PropertyRef = PropertyRef("deletion_scheduled_at")


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
    label: str = "SupabaseBranch"
    properties: SupabaseBranchNodeProperties = SupabaseBranchNodeProperties()
    sub_resource_relationship: SupabaseBranchToProjectRel = SupabaseBranchToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SupabaseBranchOfProjectRel(),
        ],
    )
