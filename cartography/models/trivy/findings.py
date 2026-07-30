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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("VulnerabilityID")
    # Every identifier the report carries for this finding, primary first. Preserved in
    # full so authorities without a dedicated field (DSA-, RHSA-, ...) are not lost.
    vulnerability_ids: PropertyRef = PropertyRef("vulnerability_ids")
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    ghsa_id: PropertyRef = PropertyRef("ghsa_id", extra_index=True)
    has_cve: PropertyRef = PropertyRef("has_cve")
    description: PropertyRef = PropertyRef("Description")
    last_modified_date: PropertyRef = PropertyRef("LastModifiedDate")
    primary_url: PropertyRef = PropertyRef("PrimaryURL")
    published_date: PropertyRef = PropertyRef("PublishedDate")
    severity: PropertyRef = PropertyRef("Severity", extra_index=True)
    severity_source: PropertyRef = PropertyRef("SeveritySource")
    title: PropertyRef = PropertyRef("Title")
    cvss_nvd_v2_score: PropertyRef = PropertyRef("nvd_v2_score")
    cvss_nvd_v2_vector: PropertyRef = PropertyRef("nvd_v2_vector")
    cvss_nvd_v3_score: PropertyRef = PropertyRef("nvd_v3_score")
    cvss_nvd_v3_vector: PropertyRef = PropertyRef("nvd_v3_vector")
    cvss_redhat_v3_score: PropertyRef = PropertyRef("redhat_v3_score")
    cvss_redhat_v3_vector: PropertyRef = PropertyRef("redhat_v3_vector")
    cvss_ubuntu_v3_score: PropertyRef = PropertyRef("ubuntu_v3_score")
    cvss_ubuntu_v3_vector: PropertyRef = PropertyRef("ubuntu_v3_vector")
    class_name: PropertyRef = PropertyRef("Class")
    type: PropertyRef = PropertyRef("Type")
    # Additional fields from Trivy scan results
    cwe_ids: PropertyRef = PropertyRef("CweIDs")
    status: PropertyRef = PropertyRef("Status")
    references: PropertyRef = PropertyRef("References")
    data_source_id: PropertyRef = PropertyRef("DataSourceID")
    data_source_name: PropertyRef = PropertyRef("DataSourceName")
    layer_digest: PropertyRef = PropertyRef("LayerDigest")
    layer_diff_id: PropertyRef = PropertyRef("LayerDiffID")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyFindingToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyFindingToOntologyImageRel(CartographyRelSchema):
    target_node_label: str = "Image"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: TrivyFindingToImageRelProperties = TrivyFindingToImageRelProperties()


@dataclass(frozen=True)
class TrivyImageFindingSchema(CartographyNodeSchema):
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
        ],
    )
