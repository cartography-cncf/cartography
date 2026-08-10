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
class ModalImageTagNodeProperties(CartographyNodeProperties):
    # Modal's tag listing has no id of its own, so the reference is synthesised as
    # "<image_id>:<tag>". One node per tag, following the same fan-out as AWS ECR
    # (`repo_uri:tag`), GitHub GHCR (`package_uri:tag`) and Scaleway.
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthesised as `<image_id>:<tag>`; Modal gives tags no id, and exposes no registry URI to use as the repository part.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    tag: PropertyRef = PropertyRef("tag", extra_index=True, description="The tag.")
    image_id: PropertyRef = PropertyRef(
        "image_id", extra_index=True, description="ID of the image it points at."
    )
    revision_id: PropertyRef = PropertyRef(
        "revision_id", description="Revision of the tag."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the tag was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the tag was last updated."
    )
    environment_name: PropertyRef = PropertyRef(
        "environment_name",
        extra_index=True,
        description="Name of the owning environment.",
    )


@dataclass(frozen=True)
class ModalImageTagToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalEnvironment)-[:RESOURCE]->(:ModalImageTag)
class ModalImageTagToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "ModalEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ENVIRONMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalImageTagToEnvironmentRelProperties = (
        ModalImageTagToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class ModalImageTagToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalImageTag)-[:IMAGE]->(:ModalImage)
# IMAGE in the OUTWARD direction is the cross-registry tag -> image edge used by AWS ECR,
# GitHub, GitLab, GCP Artifact Registry and Scaleway, so the label and direction match those.
class ModalImageTagToImageRel(CartographyRelSchema):
    target_node_label: str = "ModalImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("image_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: ModalImageTagToImageRelProperties = ModalImageTagToImageRelProperties()


@dataclass(frozen=True)
# A named pointer to a Modal image. Several tags can point at the same image, so they are
# separate nodes rather than a property on the image: keying on the image alone made every tag
# but the last one vanish on load.
#
# Deliberately NOT labelled with the ontology `ImageTag`, for the same reason ModalImage is not
# labelled `Image`. That pair of labels exists to let the supply-chain matchers traverse
# (:Image)<-[:IMAGE]-(:ImageTag)<-[:REPO_IMAGE]-(:ContainerRegistry) and join on a digest.
# Modal's tag listing returns no digest at all, so a labelled Modal tag would be a dangling
# pointer in every cross-provider image query. The structural shape is kept; only the ontology
# claim is withheld.
class ModalImageTagSchema(CartographyNodeSchema):
    """Represents a named pointer to a Modal image. Several tags can point at the same image, which is why they are separate nodes: keying on the image alone made every tag but the last vanish on load. This mirrors AWS ECR, GitHub GHCR, GitLab, GCP Artifact Registry and Scaleway, which all fan out one tag node per `(repository, tag)` pair. Deliberately **not** labelled with the ontology `ImageTag`, for the same reason `ModalImage` is not labelled `Image`. That pair exists so the supply-chain matchers can traverse `(:Image)<-[:IMAGE]-(:ImageTag)<-[:REPO_IMAGE]-(:ContainerRegistry)` and join on a digest. Modal's tag listing returns no digest, so a labelled Modal tag would be a dangling pointer in every cross-provider image query. The structural shape is kept; only the ontology claim is withheld."""

    label: str = "ModalImageTag"
    properties: ModalImageTagNodeProperties = ModalImageTagNodeProperties()
    sub_resource_relationship: ModalImageTagToEnvironmentRel = (
        ModalImageTagToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalImageTagToImageRel()],
    )
