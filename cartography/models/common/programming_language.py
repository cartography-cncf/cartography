from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class ProgrammingLanguageNodeProperties(CartographyNodeProperties):
    """Properties for a programming language."""

    id: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class ProgrammingLanguageSchema(CartographyNodeSchema):
    label: str = "ProgrammingLanguage"
    properties: ProgrammingLanguageNodeProperties = ProgrammingLanguageNodeProperties()
