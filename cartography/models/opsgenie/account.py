from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class OpsgenieAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Opsgenie account name.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Opsgenie account name.")
    user_count: PropertyRef = PropertyRef(
        "user_count",
        description="Number of users in the account.",
    )
    plan_name: PropertyRef = PropertyRef(
        "plan_name",
        description="Name of the account plan.",
    )
    max_user_count: PropertyRef = PropertyRef(
        "max_user_count",
        description="Maximum users allowed by the account plan.",
    )


@dataclass(frozen=True)
class OpsgenieAccountSchema(CartographyNodeSchema):
    """An Opsgenie account."""

    label: str = "OpsgenieAccount"
    properties: OpsgenieAccountNodeProperties = OpsgenieAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
