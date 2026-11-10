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
class NeonRoleNodeProperties(CartographyNodeProperties):
    # Role names are only unique within a branch, and every branch carries its own
    # copy of its parent's roles.
    id: PropertyRef = PropertyRef(
        "id", description="Synthesised as `<branch id>/<role name>`"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The Postgres role name"
    )
    branch_id: PropertyRef = PropertyRef(
        "branch_id", description="Id of the branch the role exists on"
    )
    protected: PropertyRef = PropertyRef(
        "protected",
        description="Whether this is a system role Neon manages and users cannot modify",
    )
    authentication_method: PropertyRef = PropertyRef(
        "authentication_method",
        description="How the role authenticates (`password`, `no_login`, ...)",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the role was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the role was last changed"
    )


@dataclass(frozen=True)
class NeonRoleToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonProject)-[:RESOURCE]->(:NeonRole)
class NeonRoleToProjectRel(CartographyRelSchema):
    target_node_label: str = "NeonProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NeonRoleToProjectRelProperties = NeonRoleToProjectRelProperties()


@dataclass(frozen=True)
class NeonRoleToBranchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonBranch)-[:CONTAINS]->(:NeonRole)
class NeonRoleToBranchRel(CartographyRelSchema):
    target_node_label: str = "NeonBranch"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("branch_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: NeonRoleToBranchRelProperties = NeonRoleToBranchRelProperties()


@dataclass(frozen=True)
class NeonRoleSchema(CartographyNodeSchema):
    """Represents a Postgres role on a Neon branch. The listing can carry a role password, which is dropped and never stored."""

    label: str = "NeonRole"
    properties: NeonRoleNodeProperties = NeonRoleNodeProperties()
    sub_resource_relationship: NeonRoleToProjectRel = NeonRoleToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NeonRoleToBranchRel(),
        ],
    )
