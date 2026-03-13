from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


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
class DockerScoutPublicImageToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageToOntologyImageRel(CartographyRelSchema):
    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("target_digest")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BUILT_ON"
    properties: DockerScoutPublicImageToImageRelProperties = (
        DockerScoutPublicImageToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageSchema(CartographyNodeSchema):
    label: str = "DockerScoutPublicImage"
    scoped_cleanup: bool = False
    properties: DockerScoutPublicImageNodeProperties = (
        DockerScoutPublicImageNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DockerScoutPublicImageToOntologyImageRel()],
    )
