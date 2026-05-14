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
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    confidence: PropertyRef = PropertyRef("confidence")
    createdat: PropertyRef = PropertyRef("createdat")
    updatedat: PropertyRef = PropertyRef("updatedat")
    eventfirstseen: PropertyRef = PropertyRef("eventfirstseen")
    eventlastseen: PropertyRef = PropertyRef("eventlastseen")
    accountid: PropertyRef = PropertyRef("accountid")
    region: PropertyRef = PropertyRef("region")
    detectorid: PropertyRef = PropertyRef("detectorid")
    resource_type: PropertyRef = PropertyRef("resource_type")
    resource_id: PropertyRef = PropertyRef("resource_id")
    archived: PropertyRef = PropertyRef("archived")
    # Service-level fields (apply to all action types)
    service_action_type: PropertyRef = PropertyRef("service_action_type")
    service_count: PropertyRef = PropertyRef("service_count")
    service_resource_role: PropertyRef = PropertyRef("service_resource_role")
    # AwsApiCallAction fields (None for non-AWS_API_CALL findings)
    api_call_name: PropertyRef = PropertyRef("api_call_name")
    api_call_service_name: PropertyRef = PropertyRef("api_call_service_name")
    api_call_caller_type: PropertyRef = PropertyRef("api_call_caller_type")
    api_call_error_code: PropertyRef = PropertyRef("api_call_error_code")
    api_call_remote_ip: PropertyRef = PropertyRef("api_call_remote_ip")
    api_call_remote_country: PropertyRef = PropertyRef("api_call_remote_country")
    api_call_remote_city: PropertyRef = PropertyRef("api_call_remote_city")
    api_call_remote_org: PropertyRef = PropertyRef("api_call_remote_org")
    api_call_remote_asn: PropertyRef = PropertyRef("api_call_remote_asn")
    api_call_remote_asn_org: PropertyRef = PropertyRef("api_call_remote_asn_org")
    api_call_remote_isp: PropertyRef = PropertyRef("api_call_remote_isp")
    api_call_remote_lat: PropertyRef = PropertyRef("api_call_remote_lat")
    api_call_remote_lon: PropertyRef = PropertyRef("api_call_remote_lon")
    api_call_remote_account_id: PropertyRef = PropertyRef(
        "api_call_remote_account_id",
        extra_index=True,
    )
    api_call_remote_account_affiliated: PropertyRef = PropertyRef(
        "api_call_remote_account_affiliated",
    )
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
class GuardDutyFindingTriggeredByAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingTriggeredByAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("api_call_remote_account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REMOTE_ACCOUNT"
    properties: GuardDutyFindingTriggeredByAWSAccountRelRelProperties = (
        GuardDutyFindingTriggeredByAWSAccountRelRelProperties()
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk", "SecurityIssue"])
    sub_resource_relationship: GuardDutyFindingToAWSAccountRel = (
        GuardDutyFindingToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GuardDutyFindingToGuardDutyDetectorRel(),
            GuardDutyFindingTriggeredByAWSAccountRel(),
            GuardDutyFindingToEC2InstanceRel(),
            GuardDutyFindingToS3BucketRel(),
        ],
    )
