from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class HuntressAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Huntress account ID, which identifies the tenant.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Public facing display name for the account.",
    )
    subdomain: PropertyRef = PropertyRef(
        "subdomain",
        extra_index=True,
        description="Subdomain the account is reached at, as `<subdomain>.huntress.io`.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Account status: `enabled` or `disabled`.",
    )
    support_type: PropertyRef = PropertyRef(
        "support_type",
        description=(
            "For accounts provisioned through a reseller, whether the account is "
            "`huntress_supported`, `partner_supported` or `not_applicable`."
        ),
    )


@dataclass(frozen=True)
class HuntressAccountSchema(CartographyNodeSchema):
    """The Huntress account the API credentials belong to."""

    label: str = "HuntressAccount"
    properties: HuntressAccountNodeProperties = HuntressAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
