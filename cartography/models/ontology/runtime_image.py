from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class RuntimeImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    digest: PropertyRef = PropertyRef("digest")
    uri: PropertyRef = PropertyRef("uri")
    runtime_refs: PropertyRef = PropertyRef("runtime_refs")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RuntimeImageHasImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RuntimeImageToContainerRel(CartographyRelSchema):
    target_node_label: str = "Container"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("container_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_IMAGE"
    properties: RuntimeImageHasImageRelProperties = RuntimeImageHasImageRelProperties()


@dataclass(frozen=True)
class RuntimeImageToFunctionRel(CartographyRelSchema):
    target_node_label: str = "Function"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("function_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_IMAGE"
    properties: RuntimeImageHasImageRelProperties = RuntimeImageHasImageRelProperties()


@dataclass(frozen=True)
class RuntimeImageSchema(CartographyNodeSchema):
    label: str = "RuntimeImage"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Image", "Ontology"])
    properties: RuntimeImageNodeProperties = RuntimeImageNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [RuntimeImageToContainerRel(), RuntimeImageToFunctionRel()],
    )
