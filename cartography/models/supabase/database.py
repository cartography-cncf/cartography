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
    id: PropertyRef = PropertyRef(
        "id", description="Synthesised as `<project ref>/postgres`"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="Display name, derived from the project name"
    )
    host: PropertyRef = PropertyRef(
        "host", extra_index=True, description="The database hostname"
    )
    version: PropertyRef = PropertyRef("version", description="The Postgres version")
    postgres_engine: PropertyRef = PropertyRef(
        "postgres_engine", description="The major Postgres engine version"
    )
    release_channel: PropertyRef = PropertyRef(
        "release_channel", description="The release channel the database runs on"
    )
    region: PropertyRef = PropertyRef(
        "region", description="The region hosting the database"
    )

    # Posture, rolled up from /ssl-enforcement, /network-restrictions and
    # /database/backups.
    ssl_enforced: PropertyRef = PropertyRef(
        "ssl_enforced", description="Whether TLS is required for database connections"
    )
    network_restrictions_status: PropertyRef = PropertyRef(
        "network_restrictions_status",
        description="Status of the project's network restriction configuration",
    )
    db_allowed_cidrs: PropertyRef = PropertyRef(
        "db_allowed_cidrs",
        description="IPv4 CIDRs allowed to reach the database. An empty or absent value means unrestricted",
    )
    db_allowed_cidrs_v6: PropertyRef = PropertyRef(
        "db_allowed_cidrs_v6", description="IPv6 CIDRs allowed to reach the database"
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="`True` when the allowed-CIDR lists leave the Postgres endpoint reachable from anywhere, either by being empty or by listing `0.0.0.0/0` or `::/0`.",
    )
    exposed_internet_type: PropertyRef = PropertyRef(
        "exposed_internet_type",
        extra_index=True,
        description="How it is exposed. Always `direct`, since the endpoint is on the database itself.",
    )
    pitr_enabled: PropertyRef = PropertyRef(
        "pitr_enabled", description="Whether point-in-time recovery is enabled"
    )
    walg_enabled: PropertyRef = PropertyRef(
        "walg_enabled", description="Whether WAL-G physical backups are enabled"
    )
    latest_backup_at: PropertyRef = PropertyRef(
        "latest_backup_at", description="Timestamp of the most recent backup"
    )


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
    """Represents the Postgres database backing a Supabase project, together with its network, TLS and backup posture."""

    label: str = "SupabaseDatabase"
    properties: SupabaseDatabaseNodeProperties = SupabaseDatabaseNodeProperties()
    sub_resource_relationship: SupabaseDatabaseToProjectRel = (
        SupabaseDatabaseToProjectRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABASE])
