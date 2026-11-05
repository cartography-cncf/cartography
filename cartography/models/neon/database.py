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
from cartography.models.ontology.labels import DATABASE


@dataclass(frozen=True)
class NeonDatabaseNodeProperties(CartographyNodeProperties):
    # Database names are only unique within a branch, and every branch carries its
    # own copy of its parent's databases.
    id: PropertyRef = PropertyRef(
        "id", description="Synthesised as `<branch id>/<database name>`"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    database_id: PropertyRef = PropertyRef(
        "database_id", description="The numeric database id returned by the API"
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The Postgres database name"
    )
    owner_name: PropertyRef = PropertyRef(
        "owner_name", description="Name of the role that owns the database"
    )
    branch_id: PropertyRef = PropertyRef(
        "branch_id", description="Id of the branch the database exists on"
    )
    host: PropertyRef = PropertyRef(
        "host",
        extra_index=True,
        description="Hostname of the branch's read-write compute, which is how clients reach this database. Absent when the branch has no read-write compute",
    )
    pg_version: PropertyRef = PropertyRef(
        "pg_version", description="The major Postgres version, from the project"
    )
    region_id: PropertyRef = PropertyRef(
        "region_id", description="The region hosting the database, from the project"
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the database was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the database was last changed"
    )


@dataclass(frozen=True)
class NeonDatabaseToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonProject)-[:RESOURCE]->(:NeonDatabase)
class NeonDatabaseToProjectRel(CartographyRelSchema):
    target_node_label: str = "NeonProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NeonDatabaseToProjectRelProperties = (
        NeonDatabaseToProjectRelProperties()
    )


@dataclass(frozen=True)
class NeonDatabaseToBranchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonBranch)-[:CONTAINS]->(:NeonDatabase)
class NeonDatabaseToBranchRel(CartographyRelSchema):
    target_node_label: str = "NeonBranch"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("branch_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: NeonDatabaseToBranchRelProperties = NeonDatabaseToBranchRelProperties()


@dataclass(frozen=True)
class NeonDatabaseToOwnerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonRole)-[:OWNS]->(:NeonDatabase)
class NeonDatabaseToOwnerRel(CartographyRelSchema):
    target_node_label: str = "NeonRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_role_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: NeonDatabaseToOwnerRelProperties = NeonDatabaseToOwnerRelProperties()


@dataclass(frozen=True)
class NeonDatabaseSchema(CartographyNodeSchema):
    """Represents a Postgres database on a Neon branch."""

    label: str = "NeonDatabase"
    properties: NeonDatabaseNodeProperties = NeonDatabaseNodeProperties()
    sub_resource_relationship: NeonDatabaseToProjectRel = NeonDatabaseToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NeonDatabaseToBranchRel(),
            NeonDatabaseToOwnerRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABASE])
