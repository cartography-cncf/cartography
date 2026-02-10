"""Ontology schema for SoftwarePackage nodes.

Provides a unified schema for software package data across different sources
(Trivy, SBOM files, native package managers, etc.).
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SoftwarePackageNodeProperties(CartographyNodeProperties):
    """Properties for SoftwarePackage ontology nodes."""

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    version: PropertyRef = PropertyRef("version")
    type: PropertyRef = PropertyRef("type")
    purl: PropertyRef = PropertyRef("purl")


@dataclass(frozen=True)
class SoftwarePackageSchema(CartographyNodeSchema):
    """Ontology schema for SoftwarePackage nodes.

    Normalizes software package data from different sources into a common format.
    Enables source-agnostic queries across Trivy scans, SBOM files, package managers, etc.
    """

    label: str = "SoftwarePackage"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: SoftwarePackageNodeProperties = SoftwarePackageNodeProperties()
    scoped_cleanup: bool = False
