from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SentryOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    date_created: PropertyRef = PropertyRef("date_created")
    require_2fa: PropertyRef = PropertyRef("require2FA", extra_index=True)
    is_early_adopter: PropertyRef = PropertyRef("isEarlyAdopter")


@dataclass(frozen=True)
class SentryOrganizationSchema(CartographyNodeSchema):
    label: str = "SentryOrganization"
    properties: SentryOrganizationNodeProperties = SentryOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
