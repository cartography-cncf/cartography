"""
Syft module data models for SyftPackage nodes.

SyftPackage nodes represent packages discovered by Syft's artifact scanner,
with DEPENDS_ON relationships between them derived from artifactRelationships.
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
class SyftPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Normalized package identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )
    name: PropertyRef = PropertyRef("name", description="Package name.")
    version: PropertyRef = PropertyRef("version", description="Package version.")
    type: PropertyRef = PropertyRef(
        "type",
        description="Package ecosystem or type, such as npm, pypi, or deb.",
    )
    purl: PropertyRef = PropertyRef(
        "purl",
        description="Package URL identifying the package.",
    )
    normalized_id: PropertyRef = PropertyRef(
        "normalized_id",
        extra_index=True,
        description="Normalized identifier used for cross-tool package matching.",
    )
    language: PropertyRef = PropertyRef(
        "language",
        description="Programming language associated with the package.",
    )
    found_by: PropertyRef = PropertyRef(
        "found_by",
        description="Syft cataloger that discovered the package.",
    )


@dataclass(frozen=True)
class SyftPackageDependsOnRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
class SyftPackageDependsOnRel(CartographyRelSchema):
    """
    Self-referential relationship: (SyftPackage)-[:DEPENDS_ON]->(SyftPackage).

    Each SyftPackage carries a dependency_ids list of normalized_ids it depends on.
    """

    target_node_label: str = "SyftPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("dependency_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPENDS_ON"
    properties: SyftPackageDependsOnRelProperties = SyftPackageDependsOnRelProperties()


@dataclass(frozen=True)
class SyftPackageToOntologyImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
class SyftPackageToOntologyImageRel(CartographyRelSchema):
    """Links a package to the ontology image in which Syft discovered it."""

    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("ImageDigestCandidates", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: SyftPackageToOntologyImageRelProperties = (
        SyftPackageToOntologyImageRelProperties()
    )


@dataclass(frozen=True)
class SyftPackageSchema(CartographyNodeSchema):
    """A software package discovered in a Syft artifact scan."""

    label: str = "SyftPackage"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([])
    properties: SyftPackageNodeProperties = SyftPackageNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SyftPackageDependsOnRel(),
            SyftPackageToOntologyImageRel(),
        ],
    )
