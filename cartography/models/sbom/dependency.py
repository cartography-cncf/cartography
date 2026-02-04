"""
DEPENDS_ON relationship schema for TrivyPackage nodes.

This module provides a MatchLink schema to create DEPENDS_ON relationships
between existing TrivyPackage nodes. This enables tracing from CVE to
transitive dependency to direct dependency.

The SBOM module uses Syft CycloneDX output to extract the dependency graph
and enriches existing TrivyPackage nodes (created by the Trivy module) with
DEPENDS_ON relationships.
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
class TrivyPackageDependsOnRelProperties(CartographyRelProperties):
    """Properties for DEPENDS_ON relationships between TrivyPackage nodes.

    Required properties for MatchLinks include lastupdated and sub-resource tracking.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )


@dataclass(frozen=True)
class TrivyPackageDependsOnMatchLink(CartographyRelSchema):
    """MatchLink schema for DEPENDS_ON relationships between TrivyPackage nodes.

    This creates relationships: (TrivyPackage)-[:DEPENDS_ON]->(TrivyPackage)
    to represent the dependency graph from Syft CycloneDX SBOM.

    The source package depends on the target package.

    TrivyPackage ID format: {version}|{name} (e.g., "3.152|adduser")
    """

    rel_label: str = "DEPENDS_ON"
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: TrivyPackageDependsOnRelProperties = (
        TrivyPackageDependsOnRelProperties()
    )

    target_node_label: str = "TrivyPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("depends_on_id")},
    )

    source_node_label: str = "TrivyPackage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("source_id")},
    )
