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
from cartography.models.ontology.labels import IMAGE
from cartography.models.ontology.labels import IMAGE_MANIFEST_LIST
from cartography.models.ontology.labels import IMAGE_TAG


@dataclass(frozen=True)
class ExternalContainerImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "digest",
        description="Global content digest used as the immutable artifact identifier.",
    )
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="OCI or Docker manifest digest.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="Resolved artifact type: `image` or `manifest_list`.",
    )
    media_type: PropertyRef = PropertyRef(
        "media_type",
        description="OCI or Docker media type reported for the manifest.",
    )
    size: PropertyRef = PropertyRef(
        "size",
        description="Manifest size in bytes, when the registry reports it.",
    )
    config_digest: PropertyRef = PropertyRef(
        "config_digest",
        description="Configuration-object digest for a single-platform image.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Creation timestamp from the digest-verified configuration object.",
    )
    os: PropertyRef = PropertyRef(
        "os",
        description="Operating system for a single-platform image.",
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description="CPU architecture for a single-platform image.",
    )
    variant: PropertyRef = PropertyRef(
        "variant",
        description="CPU architecture variant for a single-platform image.",
    )
    child_image_digests: PropertyRef = PropertyRef(
        "child_image_digests",
        description="Runnable child image digests contained by a manifest list.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ExternalContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ExternalContainerImageContainsImageRel(CartographyRelSchema):
    target_node_label: str = "ExternalContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("child_image_digests", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: ExternalContainerImageRelProperties = (
        ExternalContainerImageRelProperties()
    )


@dataclass(frozen=True)
class ExternalContainerImageSchema(CartographyNodeSchema):
    """A registry-neutral, immutable image manifest or manifest list."""

    label: str = "ExternalContainerImage"
    properties: ExternalContainerImageNodeProperties = (
        ExternalContainerImageNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ExternalContainerImageContainsImageRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            IMAGE.when(type="image"),
            # An index is an aggregate, not a runnable image.
            IMAGE_MANIFEST_LIST.when(type="manifest_list"),
        ],
    )
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class ExternalContainerImageReferenceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "location",
        description="Normalized tag or digest-qualified registry location.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        extra_index=True,
        description="Normalized tag or digest-qualified registry location.",
    )
    original_reference: PropertyRef = PropertyRef(
        "original_reference",
        description="Reference supplied by the discovery source.",
    )
    registry: PropertyRef = PropertyRef(
        "registry",
        extra_index=True,
        description="Normalized registry host.",
    )
    repository: PropertyRef = PropertyRef(
        "repository",
        extra_index=True,
        description="Normalized repository path within the registry.",
    )
    tag: PropertyRef = PropertyRef(
        "tag",
        extra_index=True,
        description="Mutable tag, when this reference is tag-qualified.",
    )
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="Immutable artifact digest currently identified by this reference.",
    )
    pullable_reference: PropertyRef = PropertyRef(
        "pullable_reference",
        extra_index=True,
        description="Normalized digest-qualified reference suitable for pulling.",
    )
    reference_type: PropertyRef = PropertyRef(
        "reference_type",
        description="Reference selector type: `tag` or `digest`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ExternalContainerImageReferenceToImageRel(CartographyRelSchema):
    target_node_label: str = "ExternalContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: ExternalContainerImageRelProperties = (
        ExternalContainerImageRelProperties()
    )


@dataclass(frozen=True)
class ExternalContainerImageReferenceSchema(CartographyNodeSchema):
    """A registry location that resolves to immutable image content."""

    label: str = "ExternalContainerImageReference"
    properties: ExternalContainerImageReferenceNodeProperties = (
        ExternalContainerImageReferenceNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ExternalContainerImageReferenceToImageRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [IMAGE_TAG.when(reference_type="tag")],
    )
    scoped_cleanup: bool = False
