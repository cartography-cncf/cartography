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
class AWSMfaDeviceNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef(
        "serialnumber",
        description="The serial number of the MFA device (same as serialnumber)",
    )
    serialnumber: PropertyRef = PropertyRef(
        "serialnumber",
        extra_index=True,
        description="The serial number that uniquely identifies the MFA device",
    )

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )

    # Business fields from AWS IAM mfa devices
    username: PropertyRef = PropertyRef(
        "username",
        description="The username of the IAM user associated with the MFA device",
    )
    user_arn: PropertyRef = PropertyRef(
        "user_arn", description="The ARN of the IAM user associated with the MFA device"
    )
    enabledate: PropertyRef = PropertyRef(
        "enabledate",
        description="ISO 8601 date-time string when the MFA device was enabled",
    )
    enabledate_dt: PropertyRef = PropertyRef(
        "enabledate_dt",
        description="DateTime object representing when the MFA device was enabled",
    )


@dataclass(frozen=True)
class AWSMfaDeviceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSMfaDeviceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSMfaDevice`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSMfaDeviceToAWSAccountRelProperties = (
        AWSMfaDeviceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSMfaDeviceToAWSUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSMfaDeviceToAWSUserRel(CartographyRelSchema):
    "Represents a `MFA_DEVICE` relationship from `AWSUser` to `AWSMfaDevice`."

    target_node_label: str = "AWSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("user_arn"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MFA_DEVICE"
    properties: AWSMfaDeviceToAWSUserRelProperties = (
        AWSMfaDeviceToAWSUserRelProperties()
    )


@dataclass(frozen=True)
class AWSMfaDeviceSchema(CartographyNodeSchema):
    "Represents an `AWSMfaDevice` node in the AWS graph."

    label: str = "AWSMfaDevice"
    properties: AWSMfaDeviceNodeProperties = AWSMfaDeviceNodeProperties()
    sub_resource_relationship: AWSMfaDeviceToAWSAccountRel = (
        AWSMfaDeviceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSMfaDeviceToAWSUserRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["MfaDevice"])
