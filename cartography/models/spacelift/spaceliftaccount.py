from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class SpaceliftAccountNodeProperties(CartographyNodeProperties):
    """
    Properties for a Spacelift Account node.
    """

    id: PropertyRef = PropertyRef("id")
    spacelift_account_id: PropertyRef = PropertyRef(
        "spacelift_account_id", extra_index=True
    )
    name: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SpaceliftAccountSchema(CartographyNodeSchema):
    """
    Schema for a Spacelift Account node.
    """

    label: str = "SpaceliftAccount"
    properties: SpaceliftAccountNodeProperties = SpaceliftAccountNodeProperties()
    sub_resource_relationship = None
    other_relationships = None
