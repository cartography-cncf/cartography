from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class DockerScoutPublicImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    tag: PropertyRef = PropertyRef("tag")
    alternative_tags: PropertyRef = PropertyRef("alternative_tags")
    version: PropertyRef = PropertyRef("version")
    digest: PropertyRef = PropertyRef("digest")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageSchema(CartographyNodeSchema):
    label: str = "DockerScoutPublicImage"
    scoped_cleanup: bool = False
    properties: DockerScoutPublicImageNodeProperties = (
        DockerScoutPublicImageNodeProperties()
    )
