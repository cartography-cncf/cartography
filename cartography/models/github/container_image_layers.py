"""
GitHub Container Image Layer Schema.

Represents individual layers within container images stored in GitHub
Container Registry. Layers are identified by their diff_id (the uncompressed
sha256) and can be shared across multiple images via Docker's layer
deduplication.

See: https://distribution.github.io/distribution/spec/manifest-v2-2/
"""

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
class GitHubContainerImageLayerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "diff_id",
        description="Uncompressed layer diff ID used as the stable identifier.",
    )
    diff_id: PropertyRef = PropertyRef(
        "diff_id",
        extra_index=True,
        description="Uncompressed layer content digest used for deduplication.",
    )
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="Compressed layer digest from the image manifest.",
    )
    media_type: PropertyRef = PropertyRef(
        "media_type", description="OCI or Docker media type of the compressed layer."
    )
    size: PropertyRef = PropertyRef(
        "size", description="Compressed layer size in bytes."
    )
    is_empty: PropertyRef = PropertyRef(
        "is_empty", description="Whether the layer makes no filesystem changes."
    )
    history: PropertyRef = PropertyRef(
        "history", description="Image configuration history entry for the layer."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageLayerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageLayerToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitHubContainerImageLayer to GitHubOrganization.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubContainerImageLayerRelProperties = (
        GitHubContainerImageLayerRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageLayerToNextRel(CartographyRelSchema):
    """
    Linked-list ordering: each layer points to the next layer(s) it appears
    immediately before in some image stack.
    """

    target_node_label: str = "GitHubContainerImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("next_diff_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NEXT"
    properties: GitHubContainerImageLayerRelProperties = (
        GitHubContainerImageLayerRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageLayerSchema(CartographyNodeSchema):
    """An uncompressed container image layer identified by its diff ID."""

    label: str = "GitHubContainerImageLayer"
    properties: GitHubContainerImageLayerNodeProperties = (
        GitHubContainerImageLayerNodeProperties()
    )
    sub_resource_relationship: GitHubContainerImageLayerToOrgRel = (
        GitHubContainerImageLayerToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubContainerImageLayerToNextRel()],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ImageLayer"])
