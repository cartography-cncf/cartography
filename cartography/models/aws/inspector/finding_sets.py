"""Inspector package vulnerability findings on EC2 instances, stored once per distinct content.

Instances launched from the same image report nearly the same findings, so storing one
node per (instance, vulnerability) repeats the same data for every instance of a fleet.
Here each distinct finding is an `AWSInspectorFindingContent`, each distinct group of
contents that some instance has is an `AWSInspectorFindingSet`, and each instance's own
data, including the IDs of its findings, is on its `AWSInspectorInstanceFindings`.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.extra_labels import RISK
from cartography.models.ontology.labels import CVE


@dataclass(frozen=True)
class AWSInspectorFindingContentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Hash of the finding data that does not depend on the affected instance."
        ),
    )
    name: PropertyRef = PropertyRef("title", description="Title of the finding.")
    type: PropertyRef = PropertyRef(
        "type", description="Finding type, always `PACKAGE_VULNERABILITY`."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Finding status: `ACTIVE` or `SUPPRESSED`."
    )
    severity: PropertyRef = PropertyRef(
        "severity", description="Inspector severity assigned to the finding."
    )
    cvssscore: PropertyRef = PropertyRef(
        "cvssscore",
        extra_index=True,
        description=(
            "Inspector score, the CVSS score adjusted for the instance's network "
            "reachability and exploitability."
        ),
    )
    cvssvector: PropertyRef = PropertyRef(
        "cvssvector", description="CVSS vector of the Inspector score."
    )
    vulnerabilityid: PropertyRef = PropertyRef(
        "vulnerabilityid",
        description="Identifier of the finding's `AWSInspectorVulnerability`.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="Normalized CVE identifier of the finding's vulnerability.",
    )
    vendorseverity: PropertyRef = PropertyRef(
        "vendorseverity",
        description="Severity that the affected package's vendor assigned to the vulnerability.",
    )
    vulnerablepackageids: PropertyRef = PropertyRef(
        "vulnerablepackageids",
        description="Identifiers of the `AWSInspectorPackage` nodes the finding affects.",
    )
    fixavailable: PropertyRef = PropertyRef(
        "fixavailable",
        description="Whether a fix is available through a version update: `YES`, `NO`, or `PARTIAL`.",
    )
    exploitavailable: PropertyRef = PropertyRef(
        "exploitavailable",
        description="Whether an exploit is available for the finding: `YES` or `NO`.",
    )
    lastknownexploitat: PropertyRef = PropertyRef(
        "lastknownexploitat",
        description="Timestamp of the last known exploit associated with the finding.",
    )
    epss_score_inspector: PropertyRef = PropertyRef(
        "epss_score_inspector",
        description="Exploit Prediction Scoring System (EPSS) score, as reported by Inspector.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingContentToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSInspectorFindingContent)
class InspectorFindingContentToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InspectorFindingContentToAWSAccountRelProperties = (
        InspectorFindingContentToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class InspectorFindingContentToVulnerabilityRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSInspectorFindingContent)-[:HAS_VULNERABILITY]->(:AWSInspectorVulnerability)
class InspectorFindingContentToVulnerabilityRel(CartographyRelSchema):
    target_node_label: str = "AWSInspectorVulnerability"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vulnerabilityid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_VULNERABILITY"
    properties: InspectorFindingContentToVulnerabilityRelProperties = (
        InspectorFindingContentToVulnerabilityRelProperties()
    )


@dataclass(frozen=True)
class AWSInspectorFindingContentSchema(CartographyNodeSchema):
    """A package vulnerability finding that AWS [Inspector](https://docs.aws.amazon.com/inspector/v2/APIReference/API_Finding.html) reports on one or more EC2 instances.

    Holds everything in the finding that does not depend on which instance it was
    reported for. Instances reach it through their `AWSInspectorInstanceFindings` and
    `AWSInspectorFindingSet`.
    """

    label: str = "AWSInspectorFindingContent"
    properties: AWSInspectorFindingContentNodeProperties = (
        AWSInspectorFindingContentNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([RISK, CVE])
    sub_resource_relationship: InspectorFindingContentToAWSAccountRel = (
        InspectorFindingContentToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [InspectorFindingContentToVulnerabilityRel()],
    )


@dataclass(frozen=True)
class InspectorFindingContentToPackageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    remediation: PropertyRef = PropertyRef(
        "remediation", description="Remediation guidance for the vulnerable package."
    )
    fixedinversion: PropertyRef = PropertyRef(
        "fixedInVersion", description="Package version that fixes the vulnerability."
    )
    filepath: PropertyRef = PropertyRef(
        "filePath", description="Path of the vulnerable package on the instance."
    )
    sourcelayerhash: PropertyRef = PropertyRef(
        "sourceLayerHash",
        description="Content hash of the layer from which this relationship originated.",
    )
    sourcelambdalayerarn: PropertyRef = PropertyRef(
        "sourceLambdaLayerArn",
        description="ARN of the Lambda layer from which this relationship originated.",
    )


@dataclass(frozen=True)
# (:AWSInspectorFindingContent)-[:HAS]->(:AWSInspectorPackage)
class InspectorFindingContentToPackageMatchLink(CartographyRelSchema):
    target_node_label: str = "AWSInspectorPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("packageid")},
    )
    source_node_label: str = "AWSInspectorFindingContent"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("contentid")},
    )
    properties: InspectorFindingContentToPackageRelProperties = (
        InspectorFindingContentToPackageRelProperties()
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS"


@dataclass(frozen=True)
class AWSInspectorFindingSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Hash of the set's sorted `content_ids`."
    )
    content_ids: PropertyRef = PropertyRef(
        "content_ids",
        description=(
            "Sorted IDs of the `AWSInspectorFindingContent` nodes in the set. An "
            "instance's `finding_ids` list its findings in the same order."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingSetToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSInspectorFindingSet)
class InspectorFindingSetToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InspectorFindingSetToAWSAccountRelProperties = (
        InspectorFindingSetToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class InspectorFindingSetToContentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSInspectorFindingSet)-[:CONTAINS]->(:AWSInspectorFindingContent)
class InspectorFindingSetToContentRel(CartographyRelSchema):
    target_node_label: str = "AWSInspectorFindingContent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("content_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: InspectorFindingSetToContentRelProperties = (
        InspectorFindingSetToContentRelProperties()
    )


@dataclass(frozen=True)
class AWSInspectorFindingSetSchema(CartographyNodeSchema):
    """A distinct group of `AWSInspectorFindingContent` nodes that one or more EC2 instances report.

    Instances launched from the same image usually share a set, so a new instance links to
    an existing set instead of adding a node per finding.
    """

    label: str = "AWSInspectorFindingSet"
    properties: AWSInspectorFindingSetNodeProperties = (
        AWSInspectorFindingSetNodeProperties()
    )
    sub_resource_relationship: InspectorFindingSetToAWSAccountRel = (
        InspectorFindingSetToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [InspectorFindingSetToContentRel()],
    )


@dataclass(frozen=True)
class AWSInspectorInstanceFindingsNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the EC2 instance.")
    instanceid: PropertyRef = PropertyRef(
        "instanceid", extra_index=True, description="ID of the EC2 instance."
    )
    awsaccount: PropertyRef = PropertyRef(
        "awsaccount", description="AWS account ID that owns the instance."
    )
    imageid: PropertyRef = PropertyRef(
        "imageid", description="ID of the AMI the instance was launched from."
    )
    finding_set_id: PropertyRef = PropertyRef(
        "finding_set_id",
        description="ID of the instance's `AWSInspectorFindingSet`.",
    )
    finding_ids: PropertyRef = PropertyRef(
        "finding_ids",
        description=(
            "Inspector finding IDs, in the order of the set's `content_ids`. The "
            "finding ARN is `arn:aws:inspector2:<region>:<awsaccount>:finding/<id>`."
        ),
    )
    first_observed_at: PropertyRef = PropertyRef(
        "first_observed_at",
        description=(
            "When Inspector first observed the instance's findings. A finding first "
            "observed more than an hour later is listed in `late_content_ids`."
        ),
    )
    late_content_ids: PropertyRef = PropertyRef(
        "late_content_ids",
        description=(
            "IDs of contents that Inspector first observed on the instance more than "
            "an hour after `first_observed_at`."
        ),
    )
    late_first_observed_at: PropertyRef = PropertyRef(
        "late_first_observed_at",
        description="When Inspector first observed each content in `late_content_ids`.",
    )
    last_observed_at: PropertyRef = PropertyRef(
        "last_observed_at",
        description="Latest time Inspector updated any of the instance's findings.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="AWS Region of the instance."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorInstanceFindingsToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSInspectorInstanceFindings)
class InspectorInstanceFindingsToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InspectorInstanceFindingsToAWSAccountRelProperties = (
        InspectorInstanceFindingsToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class InspectorInstanceFindingsToMemberAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:MEMBER]->(:AWSInspectorInstanceFindings)
class InspectorInstanceFindingsToMemberAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("awsaccount")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER"
    properties: InspectorInstanceFindingsToMemberAccountRelProperties = (
        InspectorInstanceFindingsToMemberAccountRelProperties()
    )


@dataclass(frozen=True)
class InspectorInstanceFindingsToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSInspectorInstanceFindings)-[:AFFECTS]->(:AWSEC2Instance)
class InspectorInstanceFindingsToEC2InstanceRel(CartographyRelSchema):
    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instanceid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: InspectorInstanceFindingsToEC2InstanceRelProperties = (
        InspectorInstanceFindingsToEC2InstanceRelProperties()
    )


@dataclass(frozen=True)
class InspectorInstanceFindingsToSetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSInspectorInstanceFindings)-[:HAS_FINDINGS]->(:AWSInspectorFindingSet)
class InspectorInstanceFindingsToSetRel(CartographyRelSchema):
    target_node_label: str = "AWSInspectorFindingSet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("finding_set_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_FINDINGS"
    properties: InspectorInstanceFindingsToSetRelProperties = (
        InspectorInstanceFindingsToSetRelProperties()
    )


@dataclass(frozen=True)
class AWSInspectorInstanceFindingsSchema(CartographyNodeSchema):
    """The Inspector package vulnerability findings of one EC2 instance.

    Exists for every instance Inspector reports findings on, whether or not Cartography
    has synced the instance itself, and links to its `AWSEC2Instance` when that node exists.
    """

    label: str = "AWSInspectorInstanceFindings"
    properties: AWSInspectorInstanceFindingsNodeProperties = (
        AWSInspectorInstanceFindingsNodeProperties()
    )
    sub_resource_relationship: InspectorInstanceFindingsToAWSAccountRel = (
        InspectorInstanceFindingsToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            InspectorInstanceFindingsToMemberAccountRel(),
            InspectorInstanceFindingsToEC2InstanceRel(),
            InspectorInstanceFindingsToSetRel(),
        ],
    )
