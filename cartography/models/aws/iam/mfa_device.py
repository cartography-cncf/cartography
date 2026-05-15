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
    id: PropertyRef = PropertyRef("serialnumber")
    serialnumber: PropertyRef = PropertyRef("serialnumber", extra_index=True)

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from AWS IAM mfa devices
    username: PropertyRef = PropertyRef("username")
    user_arn: PropertyRef = PropertyRef("user_arn")
    enabledate: PropertyRef = PropertyRef("enabledate")
    enabledate_dt: PropertyRef = PropertyRef("enabledate_dt")


@dataclass(frozen=True)
class AWSMfaDeviceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSMfaDeviceToAWSAccountRel(CartographyRelSchema):
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
