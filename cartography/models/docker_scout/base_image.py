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
class DockerScoutBaseImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    tag: PropertyRef = PropertyRef("tag")
    alternative_tags: PropertyRef = PropertyRef("alternative_tags")
    digest: PropertyRef = PropertyRef("digest")
    size: PropertyRef = PropertyRef("size")
    flavor: PropertyRef = PropertyRef("flavor")
    os: PropertyRef = PropertyRef("os")
    runtime: PropertyRef = PropertyRef("runtime")
    is_slim: PropertyRef = PropertyRef("is_slim")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutBaseImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageBuiltFromBaseImageRel(CartographyRelSchema):
    target_node_label: str = "DockerScoutPublicImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("built_from_public_image_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BUILT_FROM"
    properties: DockerScoutBaseImageRelProperties = DockerScoutBaseImageRelProperties()


@dataclass(frozen=True)
class DockerScoutPublicImageShouldUpdateToBaseImageRelProperties(
    CartographyRelProperties,
):
    benefits: PropertyRef = PropertyRef("benefits")
    fix: PropertyRef = PropertyRef("fix")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageUpdateToBaseImageRel(CartographyRelSchema):
    target_node_label: str = "DockerScoutPublicImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("recommended_for_public_image_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SHOULD_UPDATE_TO"
    properties: DockerScoutPublicImageShouldUpdateToBaseImageRelProperties = (
        DockerScoutPublicImageShouldUpdateToBaseImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutBaseImageSchema(CartographyNodeSchema):
    label: str = "DockerScoutBaseImage"
    scoped_cleanup: bool = False
    properties: DockerScoutBaseImageNodeProperties = (
        DockerScoutBaseImageNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DockerScoutPublicImageBuiltFromBaseImageRel(),
            DockerScoutPublicImageUpdateToBaseImageRel(),
        ],
    )
