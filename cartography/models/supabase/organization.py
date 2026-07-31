from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class SupabaseOrganizationNodeProperties(CartographyNodeProperties):
    # The Management API keys organizations by slug, and projects reference their
    # parent via `organization_slug`, so slug is the stable join key here. The
    # opaque `id` is kept as a property.
    id: PropertyRef = PropertyRef("slug")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    organization_id: PropertyRef = PropertyRef("organization_id")
    name: PropertyRef = PropertyRef("name")
    plan: PropertyRef = PropertyRef("plan")
    opt_in_tags: PropertyRef = PropertyRef("opt_in_tags")
    allowed_release_channels: PropertyRef = PropertyRef("allowed_release_channels")


@dataclass(frozen=True)
class SupabaseOrganizationSchema(CartographyNodeSchema):
    label: str = "SupabaseOrganization"
    properties: SupabaseOrganizationNodeProperties = (
        SupabaseOrganizationNodeProperties()
    )
    # The organization is the root of the Supabase hierarchy, so it deliberately
    # has no sub_resource_relationship and is never cleaned up by a scoped job.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
