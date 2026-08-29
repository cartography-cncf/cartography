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
from cartography.models.ontology.labels import ONTOLOGY


@dataclass(frozen=True)
class PackageVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "normalized_id",
        description="Normalized identifier for this specific package version.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Package name.",
    )
    version: PropertyRef = PropertyRef("version", description="Package version.")
    type: PropertyRef = PropertyRef(
        "type",
        description="Package ecosystem or type.",
    )
    purl: PropertyRef = PropertyRef(
        "purl",
        description="Package URL identifying this package version.",
    )


@dataclass(frozen=True)
class PackageVersionToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:PackageVersion)-[:DETECTED_AS]->(:TrivyPackage)
@dataclass(frozen=True)
class PackageVersionToTrivyPackageRel(CartographyRelSchema):
    """A canonical package version was detected as a Trivy package."""

    target_node_label: str = "TrivyPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_AS"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


# (:PackageVersion)-[:DETECTED_AS]->(:SyftPackage)
@dataclass(frozen=True)
class PackageVersionToSyftPackageRel(CartographyRelSchema):
    """A canonical package version was detected as a Syft package."""

    target_node_label: str = "SyftPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_AS"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


# (:PackageVersion)-[:DETECTED_AS]->(:SocketDevDependency)
@dataclass(frozen=True)
class PackageVersionToSocketDevDependencyRel(CartographyRelSchema):
    """A canonical package version was detected as a Socket.dev dependency."""

    target_node_label: str = "SocketDevDependency"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_AS"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


# (:PackageVersion)-[:DETECTED_AS]->(:GitLabDependency)
@dataclass(frozen=True)
class PackageVersionToGitLabDependencyRel(CartographyRelSchema):
    """A canonical package version was detected as a GitLab dependency."""

    target_node_label: str = "GitLabDependency"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_AS"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


# (:PackageVersion)-[:DETECTED_AS]->(:GitHubDependency)
@dataclass(frozen=True)
class PackageVersionToGitHubDependencyRel(CartographyRelSchema):
    """A canonical package version was detected as a GitHub dependency."""

    target_node_label: str = "GitHubDependency"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_AS"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


# (:PackageVersion)-[:DETECTED_AS]->(:SemgrepDependency) (SemgrepGoLibrary / SemgrepNpmLibrary)
@dataclass(frozen=True)
class PackageVersionToSemgrepDependencyRel(CartographyRelSchema):
    """A canonical package version was detected as a Semgrep dependency."""

    target_node_label: str = "SemgrepDependency"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_AS"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


@dataclass(frozen=True)
class PackageVersionToOntologyImageRel(CartographyRelSchema):
    """A canonical package version is deployed on a container image."""

    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_unused_cleanup_matcher")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


@dataclass(frozen=True)
class PackageVersionToFilesystemSnapshotRel(CartographyRelSchema):
    """A canonical package version is deployed in a filesystem snapshot."""

    target_node_label: str = "FilesystemSnapshot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_unused_cleanup_matcher")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


@dataclass(frozen=True)
class PackageVersionToTrivyFixRel(CartographyRelSchema):
    """A canonical package version should be updated to an available Trivy fix."""

    target_node_label: str = "TrivyFix"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SHOULD_UPDATE_TO"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


@dataclass(frozen=True)
class PackageVersionToPackageVersionDependsOnRel(CartographyRelSchema):
    """A canonical package version depends on another package version."""

    target_node_label: str = "PackageVersion"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPENDS_ON"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


@dataclass(frozen=True)
class TrivyImageFindingToPackageVersionRel(CartographyRelSchema):
    """A Trivy finding affects a canonical package version."""

    target_node_label: str = "TrivyImageFinding"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "AFFECTS"
    properties: PackageVersionToNodeRelProperties = PackageVersionToNodeRelProperties()


@dataclass(frozen=True)
class PackageVersionSchema(CartographyNodeSchema):
    """A canonical versioned software package aggregated across inventory sources."""

    label: str = "PackageVersion"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([ONTOLOGY])
    properties: PackageVersionNodeProperties = PackageVersionNodeProperties()
    scoped_cleanup: bool = False
    # Include propagated relationship types so GraphJob cleanup removes stale
    # ontology-derived edges by lastupdated on each sync run.
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            PackageVersionToTrivyPackageRel(),
            PackageVersionToSyftPackageRel(),
            PackageVersionToSocketDevDependencyRel(),
            PackageVersionToGitLabDependencyRel(),
            PackageVersionToGitHubDependencyRel(),
            PackageVersionToSemgrepDependencyRel(),
            PackageVersionToOntologyImageRel(),
            PackageVersionToFilesystemSnapshotRel(),
            PackageVersionToTrivyFixRel(),
            PackageVersionToPackageVersionDependsOnRel(),
            TrivyImageFindingToPackageVersionRel(),
        ],
    )
