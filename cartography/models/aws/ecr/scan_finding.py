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
class AWSECRScanFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthetic ID in the format `{repository_uri}/{image_digest}/{cve_id}`.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier for image finding.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        description="The finding severity (CRITICAL, HIGH, MEDIUM, LOW).",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="The description of the finding.",
    )
    uri: PropertyRef = PropertyRef(
        "uri",
        description="A link containing additional details about the security vulnerability.",
    )
    package_name: PropertyRef = PropertyRef(
        "package_name",
        description="Name of the vulnerable package.",
    )
    package_version: PropertyRef = PropertyRef(
        "package_version",
        description="Version of the vulnerable package.",
    )
    cvssscore: PropertyRef = PropertyRef(
        "cvssscore",
        extra_index=True,
        description="CVSS base score assigned to the vulnerability.",
    )
    image_digest: PropertyRef = PropertyRef(
        "image_digest",
        extra_index=True,
        description="Digest of the image this finding was detected in.",
    )
    repository_uri: PropertyRef = PropertyRef(
        "repository_uri",
        extra_index=True,
        description="URI of the ECR repository containing the scanned image.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS region containing the scanned ECR repository.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRScanFindingToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRScanFindingToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECRScanFindingToAWSAccountRelProperties = (
        ECRScanFindingToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECRScanFindingToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRScanFindingToECRImageRel(CartographyRelSchema):
    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: ECRScanFindingToECRImageRelProperties = (
        ECRScanFindingToECRImageRelProperties()
    )


@dataclass(frozen=True)
class AWSECRScanFindingSchema(CartographyNodeSchema):
    """Representation of an AWS ECR image scan finding from [`ecr.describe_image_scan_findings()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_DescribeImageScanFindings.html).

    All findings are labeled [`CVE`](#ontology-cve).
    """

    label: str = "AWSECRScanFinding"
    properties: AWSECRScanFindingNodeProperties = AWSECRScanFindingNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            RISK,
            CVE,
        ],
    )
    sub_resource_relationship: ECRScanFindingToAWSAccountRel = (
        ECRScanFindingToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRScanFindingToECRImageRel(),
        ],
    )
