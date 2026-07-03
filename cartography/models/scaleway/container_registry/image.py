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
class ScalewayContainerRegistryImageProperties(CartographyNodeProperties):
    # Base inventory properties, loaded from the registry listing. The
    # digest-addressed image content: Scaleway keys content by digest (carried
    # on tags); the "named image" from list_images is only a repository grouping
    # and is not modeled as its own node. Deduplicated by digest.
    #
    # Layer/provenance fields are intentionally NOT here: `load()` rewrites every
    # property of its schema, so a base `{digest}` load would null the fields the
    # supply_chain enrichment owns. Those live on the enrichment schema below.
    id: PropertyRef = PropertyRef("digest")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayContainerRegistryImageEnrichmentProperties(CartographyNodeProperties):
    """Full property set written by the OCI supply-chain enrichment.

    Includes the base fields (so identity/lastupdated stay set) plus the
    layer/provenance fields; used only by ``supply_chain`` so the registry
    inventory load never clears these.
    """

    id: PropertyRef = PropertyRef("digest")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    # Ordered uncompressed layer digests, from the OCI image config; feeds the
    # supply-chain dockerfile matcher.
    layer_diff_ids: PropertyRef = PropertyRef("layer_diff_ids")
    # Source provenance (code-to-cloud): the VCS repo the image was built from,
    # from OCI labels/annotations or the SLSA attestation. `source_uri` is the
    # match key for (:Image)-[:PACKAGED_FROM]->(:GitHubRepository|GitLab repo).
    source_uri: PropertyRef = PropertyRef("source_uri", extra_index=True)
    source_revision: PropertyRef = PropertyRef("source_revision")
    source_file: PropertyRef = PropertyRef("source_file")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayContainerRegistryImageToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryImage)
class ScalewayContainerRegistryImageToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayContainerRegistryImageToProjectRelProperties = (
        ScalewayContainerRegistryImageToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageToLayerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayContainerRegistryImage)-[:HAS_LAYER]->(:ScalewayContainerRegistryImageLayer)
class ScalewayContainerRegistryImageToLayerRel(CartographyRelSchema):
    target_node_label: str = "ScalewayContainerRegistryImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("layer_diff_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAYER"
    properties: ScalewayContainerRegistryImageToLayerRelProperties = (
        ScalewayContainerRegistryImageToLayerRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageSchema(CartographyNodeSchema):
    """Base image node from the registry inventory (namespaces sync).

    Does not carry layer/provenance fields or HAS_LAYER so it never overwrites
    what the supply_chain enrichment sets.
    """

    label: str = "ScalewayContainerRegistryImage"
    # Ontology `Image`: the digest-addressed content, the join target for
    # (:Container|:Function)-[:HAS_IMAGE]->(:Image) and RESOLVED_IMAGE.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Image"])
    properties: ScalewayContainerRegistryImageProperties = (
        ScalewayContainerRegistryImageProperties()
    )
    sub_resource_relationship: ScalewayContainerRegistryImageToProjectRel = (
        ScalewayContainerRegistryImageToProjectRel()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageEnrichmentSchema(CartographyNodeSchema):
    """Enrichment view written by the OCI supply-chain step: adds layer/provenance
    fields and the HAS_LAYER relationship without disturbing base inventory."""

    label: str = "ScalewayContainerRegistryImage"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Image"])
    properties: ScalewayContainerRegistryImageEnrichmentProperties = (
        ScalewayContainerRegistryImageEnrichmentProperties()
    )
    sub_resource_relationship: ScalewayContainerRegistryImageToProjectRel = (
        ScalewayContainerRegistryImageToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayContainerRegistryImageToLayerRel(),
        ]
    )
