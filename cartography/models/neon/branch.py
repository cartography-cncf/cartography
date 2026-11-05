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
class NeonBranchNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The branch id (`br-...`), unique across Neon"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the branch"
    )
    project_id: PropertyRef = PropertyRef(
        "PROJECT_ID",
        set_in_kwargs=True,
        description="Id of the project the branch belongs to",
    )
    parent_id: PropertyRef = PropertyRef(
        "parent_id",
        description="Id of the branch this one was created from. Absent on the root branch",
    )
    parent_timestamp: PropertyRef = PropertyRef(
        "parent_timestamp",
        description="Point in the parent's history the branch was created from",
    )
    default: PropertyRef = PropertyRef(
        "default", description="Whether this is the project's default branch"
    )
    primary: PropertyRef = PropertyRef(
        "primary", description="Deprecated alias of `default` still returned by the API"
    )
    protected: PropertyRef = PropertyRef(
        "protected",
        description="Whether the branch is protected. When the project's IP allowlist sets `protected_branches_only`, protected branches are the only ones it restricts",
    )
    current_state: PropertyRef = PropertyRef(
        "current_state",
        description="Lifecycle state of the branch (`init`, `ready`, ...)",
    )
    init_source: PropertyRef = PropertyRef(
        "init_source",
        description="What the branch was seeded with: `parent-data` copies the parent's data, `schema-only` copies only its schema",
    )
    creation_source: PropertyRef = PropertyRef(
        "creation_source",
        description="How the branch was created (`console`, `neonctl`, ...)",
    )
    logical_size: PropertyRef = PropertyRef(
        "logical_size", description="Logical size of the branch's data, in bytes"
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the branch was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the branch was last changed"
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at",
        description="When the branch is deleted automatically, if it has an expiry",
    )


@dataclass(frozen=True)
class NeonBranchToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonProject)-[:RESOURCE]->(:NeonBranch)
class NeonBranchToProjectRel(CartographyRelSchema):
    target_node_label: str = "NeonProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NeonBranchToProjectRelProperties = NeonBranchToProjectRelProperties()


@dataclass(frozen=True)
class NeonBranchToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonBranch)-[:BRANCHED_FROM]->(:NeonBranch)
class NeonBranchToParentRel(CartographyRelSchema):
    target_node_label: str = "NeonBranch"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BRANCHED_FROM"
    properties: NeonBranchToParentRelProperties = NeonBranchToParentRelProperties()


@dataclass(frozen=True)
class NeonBranchSchema(CartographyNodeSchema):
    """Represents a Neon branch: a copy-on-write clone of the project's data, together with its object storage buckets, roles and databases. A child branch carries a copy of its parent's data, so a branch created from production holds production data."""

    label: str = "NeonBranch"
    properties: NeonBranchNodeProperties = NeonBranchNodeProperties()
    sub_resource_relationship: NeonBranchToProjectRel = NeonBranchToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NeonBranchToParentRel(),
        ],
    )
