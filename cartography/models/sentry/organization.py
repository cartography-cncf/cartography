from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SentryOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Sentry organization ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Organization name.")
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="URL-friendly organization identifier.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Current organization status.",
    )
    date_created: PropertyRef = PropertyRef(
        "date_created",
        description="ISO 8601 timestamp when the organization was created.",
    )
    require_2fa: PropertyRef = PropertyRef(
        "require2FA",
        extra_index=True,
        description="Whether the organization requires two-factor authentication.",
    )
    is_early_adopter: PropertyRef = PropertyRef(
        "isEarlyAdopter",
        description="Whether the organization is an early adopter.",
    )


@dataclass(frozen=True)
class SentryOrganizationSchema(CartographyNodeSchema):
    """A Sentry organization."""

    label: str = "SentryOrganization"
    properties: SentryOrganizationNodeProperties = SentryOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
