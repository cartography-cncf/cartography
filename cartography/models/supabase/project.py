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
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class SupabaseProjectNodeProperties(CartographyNodeProperties):
    # `ref` is the 20-character project reference used in every project-scoped
    # API path. The API also returns `id`, but it is deprecated in favour of `ref`.
    id: PropertyRef = PropertyRef(
        "ref",
        description="The project ref, the 20-character identifier used in every project-scoped API path",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ref: PropertyRef = PropertyRef(
        "ref", extra_index=True, description="The project ref"
    )
    name: PropertyRef = PropertyRef("name", description="Display name of the project")
    region: PropertyRef = PropertyRef(
        "region", description="The region hosting the project"
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Project lifecycle status (`ACTIVE_HEALTHY`, `INACTIVE`, `PAUSING`, ...)",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the project was created"
    )
    organization_slug: PropertyRef = PropertyRef(
        "organization_slug", description="Slug of the owning organization"
    )

    # Whether the legacy JWT-based anon / service_role keys are still accepted.
    legacy_api_keys_enabled: PropertyRef = PropertyRef(
        "legacy_api_keys_enabled",
        description="Whether the legacy JWT-based `anon` and `service_role` keys are still accepted",
    )

    # PostgREST exposure: which Postgres schemas are reachable over the public
    # REST API, and how many rows a single anonymous request can pull.
    postgrest_db_schema: PropertyRef = PropertyRef(
        "postgrest_db_schema",
        description="The Postgres schemas exposed over the public REST API",
    )
    postgrest_max_rows: PropertyRef = PropertyRef(
        "postgrest_max_rows",
        description="Maximum rows a single REST request may return",
    )
    postgrest_db_extra_search_path: PropertyRef = PropertyRef(
        "postgrest_db_extra_search_path",
        description="Extra schemas added to the REST search path",
    )

    # Storage service configuration.
    storage_file_size_limit: PropertyRef = PropertyRef(
        "storage_file_size_limit",
        description="Maximum upload size for storage objects, in bytes",
    )
    storage_s3_protocol_enabled: PropertyRef = PropertyRef(
        "storage_s3_protocol_enabled",
        description="Whether the S3-compatible storage protocol is enabled",
    )

    # Realtime: private_only is the realtime equivalent of a private bucket.
    realtime_private_only: PropertyRef = PropertyRef(
        "realtime_private_only",
        description="Whether realtime channels require authorization",
    )
    realtime_presence_enabled: PropertyRef = PropertyRef(
        "realtime_presence_enabled", description="Whether realtime presence is enabled"
    )

    # Vanity subdomain, when configured.
    vanity_subdomain: PropertyRef = PropertyRef(
        "vanity_subdomain",
        description="The project's vanity subdomain, when configured",
    )
    vanity_subdomain_status: PropertyRef = PropertyRef(
        "vanity_subdomain_status",
        description="Status of the vanity subdomain configuration",
    )


@dataclass(frozen=True)
class SupabaseProjectToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseOrganization)-[:RESOURCE]->(:SupabaseProject)
class SupabaseProjectToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "SupabaseOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_SLUG", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseProjectToOrganizationRelProperties = (
        SupabaseProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SupabaseProjectSchema(CartographyNodeSchema):
    """Represents a Supabase project: the isolation boundary containing a Postgres database, an auth service, storage buckets and edge functions."""

    label: str = "SupabaseProject"
    properties: SupabaseProjectNodeProperties = SupabaseProjectNodeProperties()
    sub_resource_relationship: SupabaseProjectToOrganizationRel = (
        SupabaseProjectToOrganizationRel()
    )
    # A project is Supabase's isolation boundary and the sub resource for every
    # resource below it, so it carries Tenant alongside ScalewayProject / AWSAccount.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
