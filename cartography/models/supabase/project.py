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
    id: PropertyRef = PropertyRef("ref")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    ref: PropertyRef = PropertyRef("ref", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    region: PropertyRef = PropertyRef("region")
    status: PropertyRef = PropertyRef("status")
    created_at: PropertyRef = PropertyRef("created_at")
    organization_slug: PropertyRef = PropertyRef("organization_slug")

    # Whether the legacy JWT-based anon / service_role keys are still accepted.
    legacy_api_keys_enabled: PropertyRef = PropertyRef("legacy_api_keys_enabled")

    # PostgREST exposure: which Postgres schemas are reachable over the public
    # REST API, and how many rows a single anonymous request can pull.
    postgrest_db_schema: PropertyRef = PropertyRef("postgrest_db_schema")
    postgrest_max_rows: PropertyRef = PropertyRef("postgrest_max_rows")
    postgrest_db_extra_search_path: PropertyRef = PropertyRef(
        "postgrest_db_extra_search_path",
    )

    # Storage service configuration.
    storage_file_size_limit: PropertyRef = PropertyRef("storage_file_size_limit")
    storage_s3_protocol_enabled: PropertyRef = PropertyRef(
        "storage_s3_protocol_enabled",
    )

    # Realtime: private_only is the realtime equivalent of a private bucket.
    realtime_private_only: PropertyRef = PropertyRef("realtime_private_only")
    realtime_presence_enabled: PropertyRef = PropertyRef("realtime_presence_enabled")

    # Vanity subdomain, when configured.
    vanity_subdomain: PropertyRef = PropertyRef("vanity_subdomain")
    vanity_subdomain_status: PropertyRef = PropertyRef("vanity_subdomain_status")


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
    label: str = "SupabaseProject"
    properties: SupabaseProjectNodeProperties = SupabaseProjectNodeProperties()
    sub_resource_relationship: SupabaseProjectToOrganizationRel = (
        SupabaseProjectToOrganizationRel()
    )
    # A project is Supabase's isolation boundary and the sub resource for every
    # resource below it, so it carries Tenant alongside ScalewayProject / AWSAccount.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
