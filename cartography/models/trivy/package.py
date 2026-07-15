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
class TrivyPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Unique Trivy package ID.")
    installed_version: PropertyRef = PropertyRef(
        "InstalledVersion",
        description="Installed package version.",
    )
    name: PropertyRef = PropertyRef("PkgName", description="Package name.")
    version: PropertyRef = PropertyRef(
        "InstalledVersion",
        description="Installed package version.",
    )
    class_name: PropertyRef = PropertyRef(
        "Class",
        description="Trivy result class, such as operating system or language package.",
    )
    type: PropertyRef = PropertyRef(
        "Type",
        description="Package ecosystem or operating system type.",
    )
    # Additional fields from Trivy scan results
    purl: PropertyRef = PropertyRef(
        "PURL",
        description="Package URL identifying the package.",
    )
    pkg_id: PropertyRef = PropertyRef(
        "PkgID",
        description="Package identifier reported by Trivy.",
    )
    # Normalized ID for cross-tool matching (format: {type}|{namespace/}{normalized_name}|{version})
    # Namespace included when present (e.g., deb packages). Uses PEP 503 normalization for Python.
    normalized_id: PropertyRef = PropertyRef(
        "normalized_id",
        extra_index=True,
        description="Normalized cross-tool package identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class TrivyPackageToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyPackageToOntologyImageRel(CartographyRelSchema):
    """Links a Trivy package to the container image where it is installed."""

    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: TrivyPackageToImageRelProperties = TrivyPackageToImageRelProperties()


@dataclass(frozen=True)
class TrivyPackageToFindingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyPackageToFindingRel(CartographyRelSchema):
    """Links a Trivy finding to the vulnerable package it affects."""

    target_node_label: str = "TrivyImageFinding"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FindingId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "AFFECTS"
    properties: TrivyPackageToFindingRelProperties = (
        TrivyPackageToFindingRelProperties()
    )


@dataclass(frozen=True)
class TrivyPackageSchema(CartographyNodeSchema):
    """A package detected by Trivy in a container image."""

    label: str = "TrivyPackage"
    scoped_cleanup: bool = False
    properties: TrivyPackageNodeProperties = TrivyPackageNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TrivyPackageToOntologyImageRel(),
            TrivyPackageToFindingRel(),
        ],
    )
