from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSInspectorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this `AWSInspectorFinding` node."
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSInspectorFinding` node.",
    )
    awsaccount: PropertyRef = PropertyRef(
        "awsaccount",
        description="AWS account ID containing the affected resource.",
    )
    name: PropertyRef = PropertyRef(
        "title", description="Name of this `AWSInspectorFinding` node."
    )
    instanceid: PropertyRef = PropertyRef(
        "instanceid",
        description="Identifier of the instance linked to this `AWSInspectorFinding` node.",
    )
    ecrimageid: PropertyRef = PropertyRef(
        "ecrimageid",
        description="Identifier of the ecrimageid linked to this `AWSInspectorFinding` node.",
    )
    ecrrepositoryid: PropertyRef = PropertyRef(
        "ecrrepositoryid",
        description="Identifier of the ecrrepositoryid linked to this `AWSInspectorFinding` node.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        description="Inspector severity assigned to the finding.",
    )
    firstobservedat: PropertyRef = PropertyRef(
        "firstobservedat",
        description="Timestamp when Inspector first observed the vulnerability.",
    )
    updatedat: PropertyRef = PropertyRef(
        "updatedat",
        description="Timestamp when Inspector last updated the finding.",
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of this `AWSInspectorFinding` node."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Type of this `AWSInspectorFinding` node."
    )
    cvssscore: PropertyRef = PropertyRef(
        "cvssscore",
        extra_index=True,
        description="CVSS base score assigned to the vulnerability.",
    )
    protocol: PropertyRef = PropertyRef(
        "protocol",
        description="Network protocol associated with the exposed port range.",
    )
    portrange: PropertyRef = PropertyRef(
        "portrange",
        description="Formatted network port range associated with the finding.",
    )
    portrangebegin: PropertyRef = PropertyRef(
        "portrangebegin",
        description="Lowest network port associated with the finding.",
    )
    portrangeend: PropertyRef = PropertyRef(
        "portrangeend",
        description="Highest network port associated with the finding.",
    )
    vulnerabilityid: PropertyRef = PropertyRef(
        "vulnerabilityid",
        description="Identifier of the vulnerabilityid linked to this `AWSInspectorFinding` node.",
    )
    referenceurls: PropertyRef = PropertyRef(
        "referenceurls",
        description="Reference URLs describing the vulnerability.",
    )
    relatedvulnerabilities: PropertyRef = PropertyRef(
        "relatedvulnerabilities",
        description="Identifiers of vulnerabilities related to this finding.",
    )
    source: PropertyRef = PropertyRef(
        "source", description="Advisory source that reported the vulnerability."
    )
    sourceurl: PropertyRef = PropertyRef(
        "sourceurl",
        description="URL of the source advisory for the vulnerability.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="Current status of this `AWSInspectorFinding` node."
    )
    vendorcreatedat: PropertyRef = PropertyRef(
        "vendorcreatedat",
        description="Timestamp when the package vendor created the advisory.",
    )
    vendorseverity: PropertyRef = PropertyRef(
        "vendorseverity",
        description="Severity assigned by the package vendor.",
    )
    vendorupdatedat: PropertyRef = PropertyRef(
        "vendorupdatedat",
        description="Timestamp when the package vendor last updated the advisory.",
    )
    vulnerablepackageids: PropertyRef = PropertyRef(
        "vulnerablepackageids",
        description="Identifiers of packages affected by the vulnerability.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSInspectorFinding` node.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSInspectorFinding` node.",
    )


@dataclass(frozen=True)
class InspectorFindingToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSInspectorFinding`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InspectorFindingToAWSAccountRelRelProperties = (
        InspectorFindingToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class InspectorFindingToAWSAccountRelDelegateRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToAWSAccountRelDelegateRel(CartographyRelSchema):
    "Represents a `MEMBER` relationship from `AWSAccount` to `AWSInspectorFinding`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("awsaccount")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER"
    properties: InspectorFindingToAWSAccountRelDelegateRelRelProperties = (
        InspectorFindingToAWSAccountRelDelegateRelRelProperties()
    )


@dataclass(frozen=True)
class InspectorFindingToEC2InstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToEC2InstanceRel(CartographyRelSchema):
    "Represents a `AFFECTS` relationship from `AWSInspectorFinding` to `AWSEC2Instance`."

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instanceid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: InspectorFindingToEC2InstanceRelRelProperties = (
        InspectorFindingToEC2InstanceRelRelProperties()
    )


@dataclass(frozen=True)
class InspectorFindingToECRRepositoryRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToECRRepositoryRel(CartographyRelSchema):
    "Represents a `AFFECTS` relationship from `AWSInspectorFinding` to `AWSECRRepository`."

    target_node_label: str = "AWSECRRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ecrrepositoryid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: InspectorFindingToECRRepositoryRelRelProperties = (
        InspectorFindingToECRRepositoryRelRelProperties()
    )


@dataclass(frozen=True)
class InspectorFindingToECRImageRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToECRImageRel(CartographyRelSchema):
    "Represents a `AFFECTS` relationship from `AWSInspectorFinding` to `AWSECRImage`."

    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ecrimageid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: InspectorFindingToECRImageRelRelProperties = (
        InspectorFindingToECRImageRelRelProperties()
    )


@dataclass(frozen=True)
class InspectorFindingToPackageRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    # The following properties live in vulnerablePackages from AWS API
    # Adding them here to avoid multiple repetion of packages
    filepath: PropertyRef = PropertyRef(
        "filePath",
        description="Path of the vulnerable file associated with this relationship.",
    )
    fixedinversion: PropertyRef = PropertyRef(
        "fixedInVersion",
        description="Package version that fixes the vulnerability represented by this relationship.",
    )
    remediation: PropertyRef = PropertyRef(
        "remediation",
        description="Recommended remediation for the finding in this relationship.",
    )
    sourcelayerhash: PropertyRef = PropertyRef(
        "sourceLayerHash",
        description="Content hash of the Lambda layer from which this relationship originated.",
    )
    sourcelambdalayerarn: PropertyRef = PropertyRef(
        "sourceLambdaLayerArn",
        description="ARN of the Lambda layer from which this relationship originated.",
    )


@dataclass(frozen=True)
# (:AWSInspectorFinding)-[:HAS]->(:AWSInspectorPackage)
class InspectorFindingToPackageMatchLink(CartographyRelSchema):
    "Represents a `HAS` relationship from `AWSInspectorFinding` to `AWSInspectorPackage`."

    target_node_label: str = "AWSInspectorPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("packageid")},
    )
    source_node_label: str = "AWSInspectorFinding"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("findingarn")},
    )
    properties: InspectorFindingToPackageRelRelProperties = (
        InspectorFindingToPackageRelRelProperties()
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS"


@dataclass(frozen=True)
class AWSInspectorFindingSchema(CartographyNodeSchema):
    "Represents an `AWSInspectorFinding` node in the AWS graph."

    label: str = "AWSInspectorFinding"
    properties: AWSInspectorNodeProperties = AWSInspectorNodeProperties()
    # Inspector findings are mixed: package vulnerabilities are CVE-backed while
    # network-reachability findings are configuration security issues. Label them
    # by type so each shows up in the right ontology finding family.
    # NOTE: the conditional-label mechanism removes-then-sets per entry, so a label
    # can only be driven by a single condition (two entries sharing a label would
    # clobber each other). CODE_VULNERABILITY is intentionally left unlabeled for
    # now; give it its own distinct label if/when it needs one.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "Risk",
            ConditionalNodeLabel(
                label="CVE",
                conditions={"type": "PACKAGE_VULNERABILITY"},
            ),
            ConditionalNodeLabel(
                label="SecurityIssue",
                conditions={"type": "NETWORK_REACHABILITY"},
            ),
        ],
    )
    sub_resource_relationship: InspectorFindingToAWSAccountRel = (
        InspectorFindingToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            InspectorFindingToEC2InstanceRel(),
            # TODO: Fix AWSECRRepository and AWSECRImage relationships
            InspectorFindingToECRRepositoryRel(),
            InspectorFindingToECRImageRel(),
            InspectorFindingToAWSAccountRelDelegateRel(),
        ],
    )
