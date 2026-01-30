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
class GuardDutyFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    title: PropertyRef = PropertyRef("title")
    description: PropertyRef = PropertyRef("description")
    type: PropertyRef = PropertyRef("type")
    severity: PropertyRef = PropertyRef("severity")
    confidence: PropertyRef = PropertyRef("confidence")
    eventfirstseen: PropertyRef = PropertyRef("eventfirstseen")
    eventlastseen: PropertyRef = PropertyRef("eventlastseen")
    accountid: PropertyRef = PropertyRef("accountid")
    region: PropertyRef = PropertyRef("region")
    detectorid: PropertyRef = PropertyRef("detectorid")
    resource_type: PropertyRef = PropertyRef("resource_type")
    resource_id: PropertyRef = PropertyRef("resource_id")
    archived: PropertyRef = PropertyRef("archived")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GuardDutyFindingToAWSAccountRelRelProperties = (
        GuardDutyFindingToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyFindingToEC2InstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToEC2InstanceRel(CartographyRelSchema):
    target_node_label: str = "EC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: GuardDutyFindingToEC2InstanceRelRelProperties = (
        GuardDutyFindingToEC2InstanceRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyFindingToGuardDutyDetectorRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToGuardDutyDetectorRel(CartographyRelSchema):
    target_node_label: str = "GuardDutyDetector"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("detectorid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_BY"
    properties: GuardDutyFindingToGuardDutyDetectorRelRelProperties = (
        GuardDutyFindingToGuardDutyDetectorRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyFindingToS3BucketRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToS3BucketRel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: GuardDutyFindingToS3BucketRelRelProperties = (
        GuardDutyFindingToS3BucketRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyFindingSchema(CartographyNodeSchema):
    label: str = "GuardDutyFinding"
    properties: GuardDutyFindingNodeProperties = GuardDutyFindingNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk"])
    sub_resource_relationship: GuardDutyFindingToAWSAccountRel = (
        GuardDutyFindingToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GuardDutyFindingToGuardDutyDetectorRel(),
            GuardDutyFindingToEC2InstanceRel(),
            GuardDutyFindingToS3BucketRel(),
        ],
    )
