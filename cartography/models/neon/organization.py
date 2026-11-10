from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class NeonOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="The organization id (`org-...`), used in every organization-scoped API path",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="Display name of the organization"
    )
    handle: PropertyRef = PropertyRef(
        "handle",
        extra_index=True,
        description="The organization handle shown in Console URLs",
    )
    plan: PropertyRef = PropertyRef(
        "plan", description="The organization's subscription plan"
    )
    managed_by: PropertyRef = PropertyRef(
        "managed_by",
        description="Which system manages the organization (`console`, `vercel`, ...)",
    )
    require_mfa: PropertyRef = PropertyRef(
        "require_mfa",
        description="Whether every member must have multi-factor authentication enabled",
    )
    allow_hipaa_projects: PropertyRef = PropertyRef(
        "allow_hipaa_projects",
        description="Whether the organization may create HIPAA-compliant projects",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the organization was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the organization was last changed"
    )


@dataclass(frozen=True)
class NeonOrganizationSchema(CartographyNodeSchema):
    """Represents a Neon organization: the billing and membership boundary that owns projects and organization API keys."""

    label: str = "NeonOrganization"
    properties: NeonOrganizationNodeProperties = NeonOrganizationNodeProperties()
    # The organization is the root of the Neon hierarchy, so it deliberately has
    # no sub_resource_relationship and is never cleaned up by a scoped job.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
