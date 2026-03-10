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
class DockerScoutFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("source_id")
    cve_id: PropertyRef = PropertyRef("source_id", extra_index=True)
    source: PropertyRef = PropertyRef("source")
    description: PropertyRef = PropertyRef("description")
    url: PropertyRef = PropertyRef("url")
    published_at: PropertyRef = PropertyRef("published_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    cvss_version: PropertyRef = PropertyRef("cvss_version")
    vulnerable_range: PropertyRef = PropertyRef("vulnerable_range")
    cwe_ids: PropertyRef = PropertyRef("cwe_ids")
    # EPSS (Exploit Prediction Scoring System)
    epss_score: PropertyRef = PropertyRef("epss_score")
    epss_percentile: PropertyRef = PropertyRef("epss_percentile")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutFindingToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutFindingToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: DockerScoutFindingToImageRelProperties = (
        DockerScoutFindingToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutFindingToGCPImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: DockerScoutFindingToImageRelProperties = (
        DockerScoutFindingToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutFindingToGCPPlatformImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: DockerScoutFindingToImageRelProperties = (
        DockerScoutFindingToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutFindingToGitLabImageRel(CartographyRelSchema):
    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: DockerScoutFindingToImageRelProperties = (
        DockerScoutFindingToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutFindingToPackageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutFindingToPackageRel(CartographyRelSchema):
    target_node_label: str = "DockerScoutPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PackageId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: DockerScoutFindingToPackageRelProperties = (
        DockerScoutFindingToPackageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutFindingSchema(CartographyNodeSchema):
    label: str = "DockerScoutFinding"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk", "CVE"])
    properties: DockerScoutFindingNodeProperties = DockerScoutFindingNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DockerScoutFindingToECRImageRel(),
            DockerScoutFindingToGCPImageRel(),
            DockerScoutFindingToGCPPlatformImageRel(),
            DockerScoutFindingToGitLabImageRel(),
            DockerScoutFindingToPackageRel(),
        ],
    )
