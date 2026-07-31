from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import DATABASE


@dataclass(frozen=True)
class SupabaseDatabaseNodeProperties(CartographyNodeProperties):
    # Synthesised as "<project ref>/postgres": each project hosts exactly one
    # Postgres database, and the API exposes it as a sub-object of the project
    # rather than as an addressable resource with its own id.
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    host: PropertyRef = PropertyRef("host", extra_index=True)
    version: PropertyRef = PropertyRef("version")
    postgres_engine: PropertyRef = PropertyRef("postgres_engine")
    release_channel: PropertyRef = PropertyRef("release_channel")
    region: PropertyRef = PropertyRef("region")

    # Posture, rolled up from /ssl-enforcement, /network-restrictions and
    # /database/backups.
    ssl_enforced: PropertyRef = PropertyRef("ssl_enforced")
    network_restrictions_status: PropertyRef = PropertyRef(
        "network_restrictions_status",
    )
    db_allowed_cidrs: PropertyRef = PropertyRef("db_allowed_cidrs")
    db_allowed_cidrs_v6: PropertyRef = PropertyRef("db_allowed_cidrs_v6")
    pitr_enabled: PropertyRef = PropertyRef("pitr_enabled")
    walg_enabled: PropertyRef = PropertyRef("walg_enabled")
    latest_backup_at: PropertyRef = PropertyRef("latest_backup_at")


@dataclass(frozen=True)
class SupabaseDatabaseToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseDatabase)
class SupabaseDatabaseToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseDatabaseToProjectRelProperties = (
        SupabaseDatabaseToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseDatabaseSchema(CartographyNodeSchema):
    label: str = "SupabaseDatabase"
    properties: SupabaseDatabaseNodeProperties = SupabaseDatabaseNodeProperties()
    sub_resource_relationship: SupabaseDatabaseToProjectRel = (
        SupabaseDatabaseToProjectRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABASE])
