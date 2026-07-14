from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
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
class DockerScoutPublicImageSchema(CartographyNodeSchema):
    label: str = "DockerScoutPublicImage"
    scoped_cleanup: bool = False
    properties: DockerScoutPublicImageNodeProperties = (
        DockerScoutPublicImageNodeProperties()
    )


@dataclass(frozen=True)
class DockerScoutImageBuiltOnRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )
    _module_name: PropertyRef = PropertyRef("_module_name", set_in_kwargs=True)
    _module_version: PropertyRef = PropertyRef("_module_version", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutImageBuiltOnMatchLink(CartographyRelSchema):
    target_node_label: str = "DockerScoutPublicImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("public_image_id")},
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("image_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILT_ON"
    properties: DockerScoutImageBuiltOnRelProperties = (
        DockerScoutImageBuiltOnRelProperties()
    )
