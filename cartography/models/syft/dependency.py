"""
Syft module data models for package dependency relationships.

This module defines MatchLink schemas for creating DEPENDS_ON relationships
between existing TrivyPackage nodes based on Syft's artifactRelationships.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SyftPackageDependsOnRelProperties(CartographyRelProperties):
    """Relationship properties for DEPENDS_ON relationships between packages."""

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class SyftPackageDependsOnMatchLink(CartographyRelSchema):
    """
    MatchLink schema for creating DEPENDS_ON relationships between TrivyPackage nodes.

    This schema connects a source package to its dependency (target package).
    The relationship direction is:
        (parent:TrivyPackage)-[:DEPENDS_ON]->(dependency:TrivyPackage)

    Where:
        - parent is the package that depends on another
        - dependency is the package being depended upon

    Uses normalized_id for cross-tool matching (format: {type}|{normalized_name}|{version})
    This handles naming differences between Trivy and Syft (e.g., PyNaCl vs pynacl).
    """

    source_node_label: str = "TrivyPackage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"normalized_id": PropertyRef("source_id")}
    )
    target_node_label: str = "TrivyPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("target_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPENDS_ON"
    properties: SyftPackageDependsOnRelProperties = SyftPackageDependsOnRelProperties()
