from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema, ExtraNodeLabels
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    OtherRelationships,
    TargetNodeMatcher,
)


@dataclass(frozen=True)
class AWSGuardDutyFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    arn: PropertyRef = PropertyRef("arn", extra_index=True)
    type: PropertyRef = PropertyRef("type")
    severity: PropertyRef = PropertyRef("severity")
    title: PropertyRef = PropertyRef("title")
    description: PropertyRef = PropertyRef("description")
    resource_type: PropertyRef = PropertyRef("resource_type")
    resource_id: PropertyRef = PropertyRef("resource_id")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("AWS_ID", set_in_kwargs=True)})
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GuardDutyFindingToAWSAccountRelProperties = GuardDutyFindingToAWSAccountRelProperties()


@dataclass(frozen=True)
class GuardDutyFindingToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToEC2InstanceRel(CartographyRelSchema):
    target_node_label: str = "EC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("resource_id")})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: GuardDutyFindingToEC2InstanceRelProperties = GuardDutyFindingToEC2InstanceRelProperties()


@dataclass(frozen=True)
class GuardDutyFindingToS3BucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToS3BucketRel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("resource_id")})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: GuardDutyFindingToS3BucketRelProperties = GuardDutyFindingToS3BucketRelProperties()


@dataclass(frozen=True)
class AWSGuardDutyFindingSchema(CartographyNodeSchema):
    label: str = "AWSGuardDutyFinding"
    properties: AWSGuardDutyFindingNodeProperties = AWSGuardDutyFindingNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk"])
    sub_resource_relationship: GuardDutyFindingToAWSAccountRel = GuardDutyFindingToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([
        GuardDutyFindingToEC2InstanceRel(),
        GuardDutyFindingToS3BucketRel(),
    ])
