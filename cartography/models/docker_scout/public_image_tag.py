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
class DockerScoutPublicImageTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    tag: PropertyRef = PropertyRef("tag")
    alternative_tags: PropertyRef = PropertyRef("alternative_tags")
    size: PropertyRef = PropertyRef("size")
    flavor: PropertyRef = PropertyRef("flavor")
    os: PropertyRef = PropertyRef("os")
    runtime: PropertyRef = PropertyRef("runtime")
    is_slim: PropertyRef = PropertyRef("is_slim")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageBuiltFromPublicImageTagRel(CartographyRelSchema):
    target_node_label: str = "DockerScoutPublicImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("built_from_public_image_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BUILT_FROM"
    properties: DockerScoutPublicImageTagRelProperties = (
        DockerScoutPublicImageTagRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageShouldUpdateToPublicImageTagRelProperties(
    CartographyRelProperties,
):
    benefits: PropertyRef = PropertyRef("benefits")
    fix_critical: PropertyRef = PropertyRef("fix_critical")
    fix_high: PropertyRef = PropertyRef("fix_high")
    fix_medium: PropertyRef = PropertyRef("fix_medium")
    fix_low: PropertyRef = PropertyRef("fix_low")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageUpdateToPublicImageTagRel(CartographyRelSchema):
    target_node_label: str = "DockerScoutPublicImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("recommended_for_public_image_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SHOULD_UPDATE_TO"
    properties: DockerScoutPublicImageShouldUpdateToPublicImageTagRelProperties = (
        DockerScoutPublicImageShouldUpdateToPublicImageTagRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageTagSchema(CartographyNodeSchema):
    label: str = "DockerScoutPublicImageTag"
    scoped_cleanup: bool = False
    properties: DockerScoutPublicImageTagNodeProperties = (
        DockerScoutPublicImageTagNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DockerScoutPublicImageBuiltFromPublicImageTagRel(),
            DockerScoutPublicImageUpdateToPublicImageTagRel(),
        ],
    )
