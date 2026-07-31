from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ModalImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    environment_name: PropertyRef = PropertyRef("environment_name", extra_index=True)
    # NOTE: no `tag` here. One image can be published under several tags, and keying the node
    # on the image id meant every tag but the last was silently lost on load. Tags are
    # ModalImageTag nodes pointing at this one, as every other registry provider does.


@dataclass(frozen=True)
class ModalImageToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalImage)
class ModalImageToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalImageToEnvironmentRelProperties = (
        ModalImageToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
# A named/published Modal image.
#
# This node deliberately does NOT carry the ontology `Image` label. That label means a
# concrete, digest-addressed single-platform image and drives the RESOLVED_IMAGE /
# HAS_RUNTIME_IMAGE analysis. A Modal image id is neither a digest nor a pull URI, so
# tagging it would inject nodes that can never be joined against a registry image.
#
# Only *named* images are enumerable: anonymous build images (the common case, e.g. an
# inline `Image.debian_slim()`) are not returned by the API and are therefore absent.
# Cleanup is safe within the named-image universe only.
#
# Deduplicated by image id: Modal's listing is per tag, so several rows can describe one image.
class ModalImageSchema(CartographyNodeSchema):
    label: str = "ModalImage"
    properties: ModalImageNodeProperties = ModalImageNodeProperties()
    sub_resource_relationship: ModalImageToEnvironmentRel = ModalImageToEnvironmentRel()
