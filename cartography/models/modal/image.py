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
    id: PropertyRef = PropertyRef(
        "id", description="Image ID, e.g. `im-m0JhBY9qYlH5iisTrhhftT`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the image was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the image was last updated."
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )
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
    """Represents a named, published Modal image. This node deliberately carries **no** `Image` ontology label. That label means a concrete, digest-addressed single-platform image and drives the `RESOLVED_IMAGE` / `HAS_RUNTIME_IMAGE` analysis; a Modal image id is neither a digest nor a pull URI, so tagging it would inject nodes that can never be joined against a registry image. Only **named** images are enumerable. Anonymous build images (the common case, such as an inline `Image.debian_slim()`) are not returned by the API and are therefore absent, which is why a sandbox's `HAS_IMAGE` edge often does not resolve. Modal's API lists *tags*, not images, so one image published under several tags appears several times. This node is deduplicated by image id and the tags are separate `ModalImageTag` nodes."""

    label: str = "ModalImage"
    properties: ModalImageNodeProperties = ModalImageNodeProperties()
    sub_resource_relationship: ModalImageToEnvironmentRel = ModalImageToEnvironmentRel()
