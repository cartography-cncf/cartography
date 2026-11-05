from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSInspectorVulnerabilityNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Inspector vulnerability identifier, such as a CVE ID.",
    )
    vulnerabilityid: PropertyRef = PropertyRef(
        "vulnerabilityid",
        description="Inspector vulnerability identifier, such as a CVE ID.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier of the vulnerability.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Description of the vulnerability.",
    )
    referenceurls: PropertyRef = PropertyRef(
        "referenceurls",
        description=(
            "Reference URLs for the vulnerability. Inspector lists the advisories "
            "of the affected distribution, so this holds every URL reported by any "
            "finding of the vulnerability during the sync."
        ),
    )
    relatedvulnerabilities: PropertyRef = PropertyRef(
        "relatedvulnerabilities",
        description="Identifiers of vulnerabilities related to this vulnerability.",
    )
    vendorcvssvectors: PropertyRef = PropertyRef(
        "vendorcvssvectors",
        description="CVSS scoring vectors reported by the vendor and NVD sources.",
    )
    vendorcvssscores: PropertyRef = PropertyRef(
        "vendorcvssscores",
        description="CVSS base scores reported by the vendor and NVD sources.",
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="Advisory source that reported the vulnerability.",
    )
    sourceurl: PropertyRef = PropertyRef(
        "sourceurl",
        description="URL of the source advisory for the vulnerability.",
    )
    vendorcreatedat: PropertyRef = PropertyRef(
        "vendorcreatedat",
        description="Timestamp when the vendor created the vulnerability.",
    )
    vendorupdatedat: PropertyRef = PropertyRef(
        "vendorupdatedat",
        description="Timestamp when the vendor last updated the vulnerability.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorVulnerabilityToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSInspectorVulnerability)
class InspectorVulnerabilityToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InspectorVulnerabilityToAWSAccountRelProperties = (
        InspectorVulnerabilityToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSInspectorVulnerabilitySchema(CartographyNodeSchema):
    """A vulnerability that AWS [Inspector](https://docs.aws.amazon.com/inspector/v2/APIReference/API_PackageVulnerabilityDetails.html) reports in package vulnerability findings.

    Holds the advisory data that is the same for every finding of the vulnerability, so
    each `AWSInspectorFinding` stores only what is specific to one affected resource.
    """

    label: str = "AWSInspectorVulnerability"
    properties: AWSInspectorVulnerabilityNodeProperties = (
        AWSInspectorVulnerabilityNodeProperties()
    )
    sub_resource_relationship: InspectorVulnerabilityToAWSAccountRel = (
        InspectorVulnerabilityToAWSAccountRel()
    )
