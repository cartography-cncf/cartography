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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    version: PropertyRef = PropertyRef("version")
    type: PropertyRef = PropertyRef("type")
    purl: PropertyRef = PropertyRef("purl")
    normalized_id: PropertyRef = PropertyRef("normalized_id", extra_index=True)
    language: PropertyRef = PropertyRef("language")
    found_by: PropertyRef = PropertyRef("found_by")


@dataclass(frozen=True)
class SyftPackageDependsOnRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
class SyftPackageSchema(CartographyNodeSchema):
    label: str = "SyftPackage"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([])
    properties: SyftPackageNodeProperties = SyftPackageNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SyftPackageDependsOnRel(),
        ],
    )
