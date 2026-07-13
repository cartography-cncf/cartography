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
    id: PropertyRef = PropertyRef("id")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    awsaccount: PropertyRef = PropertyRef("awsaccount")
    name: PropertyRef = PropertyRef("title")
    instanceid: PropertyRef = PropertyRef("instanceid")
    ecrimageid: PropertyRef = PropertyRef("ecrimageid")
    ecrrepositoryid: PropertyRef = PropertyRef("ecrrepositoryid")
    severity: PropertyRef = PropertyRef("severity")
    firstobservedat: PropertyRef = PropertyRef("firstobservedat")
    updatedat: PropertyRef = PropertyRef("updatedat")
    description: PropertyRef = PropertyRef("description")
    type: PropertyRef = PropertyRef("type")
    cvssscore: PropertyRef = PropertyRef("cvssscore", extra_index=True)
    protocol: PropertyRef = PropertyRef("protocol")
    portrange: PropertyRef = PropertyRef("portrange")
    portrangebegin: PropertyRef = PropertyRef("portrangebegin")
    portrangeend: PropertyRef = PropertyRef("portrangeend")
    vulnerabilityid: PropertyRef = PropertyRef("vulnerabilityid")
    referenceurls: PropertyRef = PropertyRef("referenceurls")
    relatedvulnerabilities: PropertyRef = PropertyRef("relatedvulnerabilities")
    source: PropertyRef = PropertyRef("source")
    sourceurl: PropertyRef = PropertyRef("sourceurl")
    status: PropertyRef = PropertyRef("status")
    vendorcreatedat: PropertyRef = PropertyRef("vendorcreatedat")
    vendorseverity: PropertyRef = PropertyRef("vendorseverity")
    vendorupdatedat: PropertyRef = PropertyRef("vendorupdatedat")
    vulnerablepackageids: PropertyRef = PropertyRef("vulnerablepackageids")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToAWSAccountRel(CartographyRelSchema):
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
    filepath: PropertyRef = PropertyRef("filePath")
    fixedinversion: PropertyRef = PropertyRef("fixedInVersion")
    remediation: PropertyRef = PropertyRef("remediation")
    sourcelayerhash: PropertyRef = PropertyRef("sourceLayerHash")
    sourcelambdalayerarn: PropertyRef = PropertyRef("sourceLambdaLayerArn")


@dataclass(frozen=True)
# (:AWSInspectorFinding)-[:HAS]->(:AWSInspectorPackage)
class InspectorFindingToPackageMatchLink(CartographyRelSchema):
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
