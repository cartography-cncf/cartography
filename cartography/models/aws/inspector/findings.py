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
class AWSInspectorNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    arn: PropertyRef = PropertyRef('arn', extra_index=True)
    awsaccount: PropertyRef = PropertyRef('awsaccount')
    name: PropertyRef = PropertyRef('title')
    instanceid: PropertyRef = PropertyRef('instanceid')
    ecrimageid: PropertyRef = PropertyRef('ecrimageid')
    ecrrepositoryid: PropertyRef = PropertyRef('ecrrepositoryid')
    severity: PropertyRef = PropertyRef('severity')
    firstobservedat: PropertyRef = PropertyRef('firstobservedat')
    updatedat: PropertyRef = PropertyRef('updatedat')
    description: PropertyRef = PropertyRef('description')
    type: PropertyRef = PropertyRef('type')
    cvssscore: PropertyRef = PropertyRef('cvssscore', extra_index=True)
    protocol: PropertyRef = PropertyRef('protocol')
    portrange: PropertyRef = PropertyRef('portrange')
    portrangebegin: PropertyRef = PropertyRef('portrangebegin')
    portrangeend: PropertyRef = PropertyRef('portrangeend')
    vulnerabilityid: PropertyRef = PropertyRef('vulnerabilityid')
    referenceurls: PropertyRef = PropertyRef('referenceurls')
    relatedvulnerabilities: PropertyRef = PropertyRef('relatedvulnerabilities')
    source: PropertyRef = PropertyRef('source')
    sourceurl: PropertyRef = PropertyRef('sourceurl')
    status: PropertyRef = PropertyRef('status')
    vendorcreatedat: PropertyRef = PropertyRef('vendorcreatedat')
    vendorseverity: PropertyRef = PropertyRef('vendorseverity')
    vendorupdatedat: PropertyRef = PropertyRef('vendorupdatedat')
    vulnerablepackageids: PropertyRef = PropertyRef('vulnerablepackageids')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InspectorFindingToAwsAccountRelProperties = InspectorFindingToAwsAccountRelProperties()


@dataclass(frozen=True)
class InspectorFindingToAwsAccountDelegateRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToAWSAccountDelegate(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('awsaccount')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER"
    properties: InspectorFindingToAwsAccountDelegateRelProperties = InspectorFindingToAwsAccountDelegateRelProperties()


@dataclass(frozen=True)
class InspectorFindingToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToEC2Instance(CartographyRelSchema):
    target_node_label: str = 'EC2Instance'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('instanceid')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: InspectorFindingToEC2InstanceRelProperties = InspectorFindingToEC2InstanceRelProperties()


@dataclass(frozen=True)
class InspectorFindingToECRRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToECRRepository(CartographyRelSchema):
    target_node_label: str = 'ECRRepository'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('ecrrepositoryid')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: InspectorFindingToECRRepositoryRelProperties = InspectorFindingToECRRepositoryRelProperties()


@dataclass(frozen=True)
class InspectorFindingToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class InspectorFindingToECRImage(CartographyRelSchema):
    target_node_label: str = 'ECRImage'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('ecrimageid')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: InspectorFindingToECRImageRelProperties = InspectorFindingToECRImageRelProperties()


@dataclass(frozen=True)
class AWSInspectorFindingSchema(CartographyNodeSchema):
    label: str = 'AWSInspectorFinding'
    properties: AWSInspectorNodeProperties = AWSInspectorNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk"])
    sub_resource_relationship: InspectorFindingToAWSAccount = InspectorFindingToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            InspectorFindingToEC2Instance(),
            InspectorFindingToECRRepository(),
            InspectorFindingToECRImage(),
            InspectorFindingToAWSAccountDelegate(),
        ],
    )
