from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class BigfixRootNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="BigFix root URL.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class BigfixRootSchema(CartographyNodeSchema):
    """A BigFix root server containing managed computers."""

    label: str = "BigfixRoot"
    properties: BigfixRootNodeProperties = BigfixRootNodeProperties()
