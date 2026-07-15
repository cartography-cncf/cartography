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
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this `AWSGuardDutyFinding` node."
    )
    arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSGuardDutyFinding` node.",
    )
    title: PropertyRef = PropertyRef(
        "title", description="Human-readable title of the GuardDuty finding."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of this `AWSGuardDutyFinding` node."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Type of this `AWSGuardDutyFinding` node."
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="GuardDuty finding severity on its numeric severity scale.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Confidence score assigned to the GuardDuty finding.",
    )
    createdat: PropertyRef = PropertyRef(
        "createdat",
        description="Timestamp when GuardDuty created the finding.",
    )
    updatedat: PropertyRef = PropertyRef(
        "updatedat",
        description="Timestamp when GuardDuty last updated the finding.",
    )
    eventfirstseen: PropertyRef = PropertyRef(
        "eventfirstseen",
        description="Timestamp when the activity that produced the finding was first observed.",
    )
    eventlastseen: PropertyRef = PropertyRef(
        "eventlastseen",
        description="Timestamp when the activity that produced the finding was last observed.",
    )
    accountid: PropertyRef = PropertyRef(
        "accountid",
        description="Identifier of the account linked to this `AWSGuardDutyFinding` node.",
    )
    region: PropertyRef = PropertyRef(
        "region", description="AWS Region containing this `AWSGuardDutyFinding` node."
    )
    detectorid: PropertyRef = PropertyRef(
        "detectorid",
        description="Identifier of the detector linked to this `AWSGuardDutyFinding` node.",
    )
    resource_type: PropertyRef = PropertyRef(
        "resource_type",
        description="AWS resource type affected by the finding.",
    )
    resource_id: PropertyRef = PropertyRef(
        "resource_id",
        description="Identifier of the resource linked to this `AWSGuardDutyFinding` node.",
    )
    eks_cluster_arn: PropertyRef = PropertyRef(
        "eks_cluster_arn",
        extra_index=True,
        description="ARN of the EKS cluster linked to this `AWSGuardDutyFinding` node.",
    )
    access_key_id: PropertyRef = PropertyRef(
        "access_key_id",
        extra_index=True,
        description="Identifier of the access key linked to this `AWSGuardDutyFinding` node.",
    )
    principal_user_id: PropertyRef = PropertyRef(
        "principal_user_id",
        extra_index=True,
        description="Identifier of the principal user linked to this `AWSGuardDutyFinding` node.",
    )
    principal_role_id: PropertyRef = PropertyRef(
        "principal_role_id",
        extra_index=True,
        description="Identifier of the principal role linked to this `AWSGuardDutyFinding` node.",
    )
    archived: PropertyRef = PropertyRef(
        "archived",
        extra_index=True,
        description="Whether this `AWSGuardDutyFinding` node is archived.",
    )
    sample: PropertyRef = PropertyRef(
        "sample",
        description="Whether this `AWSGuardDutyFinding` node is a sample finding.",
    )
    # Service-level fields (apply to all action types)
    service_action_type: PropertyRef = PropertyRef(
        "service_action_type",
        description="GuardDuty action category associated with the finding.",
    )
    service_count: PropertyRef = PropertyRef(
        "service_count",
        description="Number of times GuardDuty observed the activity.",
    )
    service_resource_role: PropertyRef = PropertyRef(
        "service_resource_role",
        description="Role of the affected resource in the observed activity.",
    )
    # AwsApiCallAction fields (None for non-AWS_API_CALL findings)
    api_call_name: PropertyRef = PropertyRef(
        "api_call_name",
        description="Name of the API operation associated with the finding.",
    )
    api_call_service_name: PropertyRef = PropertyRef(
        "api_call_service_name",
        description="AWS service on which the API operation was invoked.",
    )
    api_call_caller_type: PropertyRef = PropertyRef(
        "api_call_caller_type",
        description="Identity category of the API caller.",
    )
    api_call_error_code: PropertyRef = PropertyRef(
        "api_call_error_code",
        description="Error code returned by the API operation, when present.",
    )
    api_call_remote_ip: PropertyRef = PropertyRef(
        "api_call_remote_ip",
        description="Remote IP address from which the API operation originated.",
    )
    api_call_remote_country: PropertyRef = PropertyRef(
        "api_call_remote_country",
        description="Country associated with the remote API caller.",
    )
    api_call_remote_city: PropertyRef = PropertyRef(
        "api_call_remote_city",
        description="City associated with the remote API caller.",
    )
    api_call_remote_org: PropertyRef = PropertyRef(
        "api_call_remote_org",
        description="Organization associated with the remote API caller.",
    )
    api_call_remote_asn: PropertyRef = PropertyRef(
        "api_call_remote_asn",
        description="Autonomous system number associated with the remote API caller.",
    )
    api_call_remote_asn_org: PropertyRef = PropertyRef(
        "api_call_remote_asn_org",
        description="Organization registered to the remote caller's autonomous system.",
    )
    api_call_remote_isp: PropertyRef = PropertyRef(
        "api_call_remote_isp",
        description="Internet service provider associated with the remote API caller.",
    )
    api_call_remote_lat: PropertyRef = PropertyRef(
        "api_call_remote_lat",
        description="Latitude associated with the remote API caller.",
    )
    api_call_remote_lon: PropertyRef = PropertyRef(
        "api_call_remote_lon",
        description="Longitude associated with the remote API caller.",
    )
    api_call_remote_account_id: PropertyRef = PropertyRef(
        "api_call_remote_account_id",
        extra_index=True,
        description="Identifier of the API call remote account linked to this `AWSGuardDutyFinding` node.",
    )
    api_call_remote_account_affiliated: PropertyRef = PropertyRef(
        "api_call_remote_account_affiliated",
        description="Whether the remote AWS account is affiliated with the affected account.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSGuardDutyFinding` node.",
    )


@dataclass(frozen=True)
class GuardDutyFindingToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSGuardDutyFinding`."

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
    "Represents a `AFFECTS` relationship from `AWSGuardDutyFinding` to `AWSEC2Instance`."

    target_node_label: str = "AWSEC2Instance"
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
    "Represents a `DETECTED_BY` relationship from `AWSGuardDutyFinding` to `AWSGuardDutyDetector`."

    target_node_label: str = "AWSGuardDutyDetector"
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
    "Represents a `REMOTE_ACCOUNT` relationship from `AWSGuardDutyFinding` to `AWSAccount`."

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
class GuardDutyFindingToEKSClusterRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToEKSClusterRel(CartographyRelSchema):
    "Represents a `AFFECTS` relationship from `AWSGuardDutyFinding` to `AWSEKSCluster`."

    target_node_label: str = "AWSEKSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("eks_cluster_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: GuardDutyFindingToEKSClusterRelRelProperties = (
        GuardDutyFindingToEKSClusterRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyFindingToS3BucketRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToS3BucketRel(CartographyRelSchema):
    "Represents a `AFFECTS` relationship from `AWSGuardDutyFinding` to `AWSS3Bucket`."

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: GuardDutyFindingToS3BucketRelRelProperties = (
        GuardDutyFindingToS3BucketRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyFindingToAccountAccessKeyRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToAccountAccessKeyRel(CartographyRelSchema):
    "Represents a `AFFECTS` relationship from `AWSGuardDutyFinding` to `AWSAccountAccessKey`."

    target_node_label: str = "AWSAccountAccessKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("access_key_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: GuardDutyFindingToAccountAccessKeyRelRelProperties = (
        GuardDutyFindingToAccountAccessKeyRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyFindingToAWSUserRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToAWSUserRel(CartographyRelSchema):
    "Represents a `AFFECTS` relationship from `AWSGuardDutyFinding` to `AWSUser`."

    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"userid": PropertyRef("principal_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: GuardDutyFindingToAWSUserRelRelProperties = (
        GuardDutyFindingToAWSUserRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyFindingToAWSRoleRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardDutyFindingToAWSRoleRel(CartographyRelSchema):
    "Represents a `AFFECTS` relationship from `AWSGuardDutyFinding` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"roleid": PropertyRef("principal_role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: GuardDutyFindingToAWSRoleRelRelProperties = (
        GuardDutyFindingToAWSRoleRelRelProperties()
    )


@dataclass(frozen=True)
class GuardDutyFindingSchema(CartographyNodeSchema):
    "Represents an `AWSGuardDutyFinding` node in the AWS graph."

    label: str = "AWSGuardDutyFinding"
    properties: GuardDutyFindingNodeProperties = GuardDutyFindingNodeProperties()
    # DEPRECATED: legacy GuardDutyFinding node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["GuardDutyFinding", "Risk", "SecurityIssue"]
    )
    sub_resource_relationship: GuardDutyFindingToAWSAccountRel = (
        GuardDutyFindingToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GuardDutyFindingToGuardDutyDetectorRel(),
            GuardDutyFindingTriggeredByAWSAccountRel(),
            GuardDutyFindingToEC2InstanceRel(),
            GuardDutyFindingToEKSClusterRel(),
            GuardDutyFindingToS3BucketRel(),
            GuardDutyFindingToAccountAccessKeyRel(),
            GuardDutyFindingToAWSUserRel(),
            GuardDutyFindingToAWSRoleRel(),
        ],
    )
