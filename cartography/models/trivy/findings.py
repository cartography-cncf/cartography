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
from cartography.models.extra_labels import RISK
from cartography.models.ontology.labels import CVE


@dataclass(frozen=True)
class TrivyImageFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Unique Trivy finding ID.")
    name: PropertyRef = PropertyRef(
        "VulnerabilityID",
        description="Vulnerability identifier reported by Trivy.",
    )
    vulnerability_ids: PropertyRef = PropertyRef(
        "vulnerability_ids",
        description="All vulnerability identifiers reported for this finding, with the primary identifier first.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier.",
    )
    ghsa_id: PropertyRef = PropertyRef(
        "ghsa_id",
        extra_index=True,
        description="GitHub Security Advisory identifier.",
    )
    has_cve: PropertyRef = PropertyRef(
        "has_cve",
        description="Whether the finding includes a CVE identifier.",
    )
    description: PropertyRef = PropertyRef(
        "Description",
        description="Vulnerability description.",
    )
    last_modified_date: PropertyRef = PropertyRef(
        "LastModifiedDate",
        description="Date the vulnerability record was last modified.",
    )
    primary_url: PropertyRef = PropertyRef(
        "PrimaryURL",
        description="Primary vulnerability reference URL.",
    )
    published_date: PropertyRef = PropertyRef(
        "PublishedDate",
        description="Date the vulnerability was published.",
    )
    severity: PropertyRef = PropertyRef(
        "Severity",
        extra_index=True,
        description=(
            "Vulnerability severity. From the last package row ingested for this "
            "finding, across all scans. Per-target severity, source and status are on "
            "AFFECTS."
        ),
    )
    severity_source: PropertyRef = PropertyRef(
        "SeveritySource",
        description=(
            "Source of the severity rating. From the last package row ingested for "
            "this finding, across all scans. Per-target severity, source and status "
            "are on AFFECTS."
        ),
    )
    title: PropertyRef = PropertyRef("Title", description="Vulnerability title.")
    cvss_nvd_v2_score: PropertyRef = PropertyRef(
        "nvd_v2_score",
        description="NVD CVSS v2 score.",
    )
    cvss_nvd_v2_vector: PropertyRef = PropertyRef(
        "nvd_v2_vector",
        description="NVD CVSS v2 vector.",
    )
    cvss_nvd_v3_score: PropertyRef = PropertyRef(
        "nvd_v3_score",
        description="NVD CVSS v3 score.",
    )
    cvss_nvd_v3_vector: PropertyRef = PropertyRef(
        "nvd_v3_vector",
        description="NVD CVSS v3 vector.",
    )
    cvss_redhat_v3_score: PropertyRef = PropertyRef(
        "redhat_v3_score",
        description="Red Hat CVSS v3 score.",
    )
    cvss_redhat_v3_vector: PropertyRef = PropertyRef(
        "redhat_v3_vector",
        description="Red Hat CVSS v3 vector.",
    )
    cvss_ubuntu_v3_score: PropertyRef = PropertyRef(
        "ubuntu_v3_score",
        description="Ubuntu CVSS v3 score.",
    )
    cvss_ubuntu_v3_vector: PropertyRef = PropertyRef(
        "ubuntu_v3_vector",
        description="Ubuntu CVSS v3 vector.",
    )
    class_name: PropertyRef = PropertyRef(
        "Class",
        description=(
            "Trivy result class, such as operating system or language package. From "
            "the last package row ingested for this finding, across all scans."
        ),
    )
    type: PropertyRef = PropertyRef(
        "Type",
        description=(
            "Trivy result type, such as an operating system or package ecosystem. "
            "From the last package row ingested for this finding, across all scans."
        ),
    )
    # Additional fields from Trivy scan results
    cwe_ids: PropertyRef = PropertyRef(
        "CweIDs",
        description="Associated CWE identifiers.",
    )
    status: PropertyRef = PropertyRef(
        "Status",
        description=(
            "Vulnerability remediation status. From the last package row ingested for "
            "this finding, across all scans. Per-target severity, source and status "
            "are on AFFECTS."
        ),
    )
    references: PropertyRef = PropertyRef(
        "References",
        description="Vulnerability reference URLs.",
    )
    data_source_id: PropertyRef = PropertyRef(
        "DataSourceID",
        description=(
            "Trivy vulnerability data source ID. From the last package row ingested "
            "for this finding, across all scans. Per-target severity, source and "
            "status are on AFFECTS."
        ),
    )
    data_source_name: PropertyRef = PropertyRef(
        "DataSourceName",
        description=(
            "Trivy vulnerability data source name. From the last package row ingested "
            "for this finding, across all scans."
        ),
    )
    layer_digest: PropertyRef = PropertyRef(
        "LayerDigest",
        description=(
            "Digest of the image layer containing the vulnerable package. From the "
            "last package row ingested for this finding, across all scans."
        ),
    )
    layer_diff_id: PropertyRef = PropertyRef(
        "LayerDiffID",
        description=(
            "Uncompressed digest of the affected image layer. From the last package "
            "row ingested for this finding, across all scans."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyFindingToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    severity: PropertyRef = PropertyRef(
        "TargetSeverity",
        description=(
            "Highest severity Trivy reported for this finding in this scan target, "
            "across every package in the target that carries it. Raw Trivy value "
            "(uppercase)."
        ),
    )
    severity_source: PropertyRef = PropertyRef(
        "TargetSeveritySource",
        description=(
            "Source Trivy named for that severity: a distribution or ecosystem "
            "advisory database such as debian, ubuntu or ghsa, or nvd for its NVD "
            "fallback. Null when Trivy used its default severity without naming a "
            "source."
        ),
    )
    status: PropertyRef = PropertyRef(
        "TargetStatus",
        description=(
            "Fix status Trivy reported with that rating, in Trivy's vocabulary "
            "(affected, fixed, will_not_fix, fix_deferred, ...). fixed means a fixed "
            "version exists; the installed package is still vulnerable. When "
            "packages tie, no fix available (affected, will_not_fix, ...) is "
            "preferred over fix available (fixed), and fixed over not_affected."
        ),
    )
    data_source_id: PropertyRef = PropertyRef(
        "TargetDataSourceID",
        description=(
            "ID of the Trivy advisory database that matched the package behind that "
            "rating."
        ),
    )


@dataclass(frozen=True)
class TrivyFindingToOntologyImageRel(CartographyRelSchema):
    """
    Links a Trivy finding to the container image it affects, with the severity, its
    source and the fix status Trivy reported for that image.
    """

    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: TrivyFindingToImageRelProperties = TrivyFindingToImageRelProperties()


@dataclass(frozen=True)
class TrivyFindingToFilesystemSnapshotRel(CartographyRelSchema):
    """
    Links a Trivy finding to the filesystem snapshots it affects, with the severity,
    its source and the fix status Trivy reported for that snapshot.
    """

    target_node_label: str = "FilesystemSnapshot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FilesystemSnapshotIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: TrivyFindingToImageRelProperties = TrivyFindingToImageRelProperties()


@dataclass(frozen=True)
class TrivyImageFindingSchema(CartographyNodeSchema):
    """A vulnerability finding detected by Trivy in a scan target."""

    label: str = "TrivyImageFinding"
    scoped_cleanup: bool = False
    # Trivy reports CVEs alongside other identifier schemes (GHSA-, DLA-, TEMP-, ...),
    # so :CVE is only applied to CVE-backed findings. :Risk covers all of them.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            RISK,
            CVE.when(has_cve="true"),
        ],
    )
    properties: TrivyImageFindingNodeProperties = TrivyImageFindingNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TrivyFindingToOntologyImageRel(),
            TrivyFindingToFilesystemSnapshotRel(),
        ],
    )
