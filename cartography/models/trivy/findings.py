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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("VulnerabilityID")
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyFindingToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyFindingToImage(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: TrivyFindingToImageRelProperties = TrivyFindingToImageRelProperties()


@dataclass(frozen=True)
class TrivyImageFindingSchema(CartographyNodeSchema):
    label: str = "TrivyImageFinding"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk", "CVE"])
    properties: TrivyImageFindingNodeProperties = TrivyImageFindingNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TrivyFindingToImage(),
        ],
    )
