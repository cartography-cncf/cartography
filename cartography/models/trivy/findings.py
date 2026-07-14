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
class TrivyImageFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Unique Trivy finding ID.")
    name: PropertyRef = PropertyRef(
        "VulnerabilityID",
        description="Vulnerability identifier reported by Trivy.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier.",
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
        description="Vulnerability severity.",
    )
    severity_source: PropertyRef = PropertyRef(
        "SeveritySource",
        description="Source of the severity rating.",
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
        description="Trivy result class, such as operating system or language package.",
    )
    type: PropertyRef = PropertyRef(
        "Type",
        description="Trivy result type, such as an operating system or package ecosystem.",
    )
    # Additional fields from Trivy scan results
    cwe_ids: PropertyRef = PropertyRef(
        "CweIDs",
        description="Associated CWE identifiers.",
    )
    status: PropertyRef = PropertyRef(
        "Status",
        description="Vulnerability remediation status.",
    )
    references: PropertyRef = PropertyRef(
        "References",
        description="Vulnerability reference URLs.",
    )
    data_source_id: PropertyRef = PropertyRef(
        "DataSourceID",
        description="Trivy vulnerability data source ID.",
    )
    data_source_name: PropertyRef = PropertyRef(
        "DataSourceName",
        description="Trivy vulnerability data source name.",
    )
    layer_digest: PropertyRef = PropertyRef(
        "LayerDigest",
        description="Digest of the image layer containing the vulnerable package.",
    )
    layer_diff_id: PropertyRef = PropertyRef(
        "LayerDiffID",
        description="Uncompressed digest of the affected image layer.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class TrivyFindingToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyFindingToOntologyImageRel(CartographyRelSchema):
    """Links a Trivy finding to the container image it affects."""

    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: TrivyFindingToImageRelProperties = TrivyFindingToImageRelProperties()


@dataclass(frozen=True)
class TrivyImageFindingSchema(CartographyNodeSchema):
    """A vulnerability finding detected by Trivy in a container image."""

    label: str = "TrivyImageFinding"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk", "CVE"])
    properties: TrivyImageFindingNodeProperties = TrivyImageFindingNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TrivyFindingToOntologyImageRel(),
        ],
    )
