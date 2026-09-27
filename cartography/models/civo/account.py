from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class CivoAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Civo account ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    default_user_id: PropertyRef = PropertyRef(
        "default_user_id", description="ID of the account's default user."
    )
    default_user_email_address: PropertyRef = PropertyRef(
        "default_user_email_address",
        extra_index=True,
        description="Email address of the account's default user.",
    )


@dataclass(frozen=True)
class CivoAccountSchema(CartographyNodeSchema):
    """A Civo account, the root tenant every other Civo resource belongs to."""

    label: str = "CivoAccount"
    properties: CivoAccountNodeProperties = CivoAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
