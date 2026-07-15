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
class ScalewayContainerRegistryImageTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Tag UUID.")
    # `name` is the tag string (e.g. "latest", "v1.2.3").
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Tag string (e.g. `latest`)."
    )
    # The repository (named image) the tag belongs to, denormalized from
    # list_images since Scaleway does not model the named image as its own node.
    image_name: PropertyRef = PropertyRef(
        "image_name",
        extra_index=True,
        description="Name of the repository (named image) the tag belongs to.",
    )
    # Full pull URI, e.g. rg.fr-par.scw.cloud/<namespace>/<image>:<tag>.
    uri: PropertyRef = PropertyRef(
        "uri",
        extra_index=True,
        description="Full pull URI, e.g. `rg.fr-par.scw.cloud/<namespace>/<image>:<tag>`.",
    )
    digest: PropertyRef = PropertyRef(
        "digest", extra_index=True, description="Digest (sha256) the tag resolves to."
    )
    status: PropertyRef = PropertyRef("status", description="Tag status.")
    # Per-image visibility (`public`, `private`, `inherit`); combined with the
    # namespace `is_public` flag it drives the public-image exposure signal.
    visibility: PropertyRef = PropertyRef(
        "visibility",
        description="Per-image visibility (`public`, `private`, `inherit`). Combined with the namespace `is_public` flag to derive effective exposure.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageTagToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryImageTag)
class ScalewayContainerRegistryImageTagToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayContainerRegistryImageTag` through
    `RESOURCE`.
    """

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayContainerRegistryImageTagToProjectRelProperties = (
        ScalewayContainerRegistryImageTagToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageTagToNamespaceRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayContainerRegistryNamespace)-[:REPO_IMAGE]->(:ScalewayContainerRegistryImageTag)
# REPO_IMAGE is the canonical cross-provider registry -> tag edge (mirrors
# AWSECRRepository / GCPArtifactRegistryRepository), consumed by the supply-chain
# code-to-cloud matchers.
class ScalewayContainerRegistryImageTagToNamespaceRel(CartographyRelSchema):
    """Connects `ScalewayContainerRegistryNamespace` to `ScalewayContainerRegistryImageTag`
    through `REPO_IMAGE`.
    """

    target_node_label: str = "ScalewayContainerRegistryNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("namespace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REPO_IMAGE"
    properties: ScalewayContainerRegistryImageTagToNamespaceRelProperties = (
        ScalewayContainerRegistryImageTagToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageTagToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayContainerRegistryImageTag)-[:IMAGE]->(:ScalewayContainerRegistryImage)
class ScalewayContainerRegistryImageTagToImageRel(CartographyRelSchema):
    """Connects `ScalewayContainerRegistryImageTag` to `ScalewayContainerRegistryImage`
    through `IMAGE`.
    """

    target_node_label: str = "ScalewayContainerRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: ScalewayContainerRegistryImageTagToImageRelProperties = (
        ScalewayContainerRegistryImageTagToImageRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageTagSchema(CartographyNodeSchema):
    """Represents a tag (a named pointer such as `latest` or `v1.2.3`) inside a Container
    Registry namespace, resolving to a specific image digest. Scaleway's namespace is
    the registry (like a GCP Artifact Registry repository), so the "named image" from
    `list_images` is not modeled as its own node; its name and visibility are
    denormalized onto the tag.
    """

    label: str = "ScalewayContainerRegistryImageTag"
    # Ontology `ImageTag`: a named pointer (tag) to a digest-addressed Image.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ImageTag"])
    properties: ScalewayContainerRegistryImageTagNodeProperties = (
        ScalewayContainerRegistryImageTagNodeProperties()
    )
    sub_resource_relationship: ScalewayContainerRegistryImageTagToProjectRel = (
        ScalewayContainerRegistryImageTagToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayContainerRegistryImageTagToNamespaceRel(),
            ScalewayContainerRegistryImageTagToImageRel(),
        ]
    )
