from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SESIdentityNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("IdentityArn")
    arn: PropertyRef = PropertyRef("IdentityArn", extra_index=True)
    identity: PropertyRef = PropertyRef("Identity", extra_index=True)
    identity_type: PropertyRef = PropertyRef("IdentityType")
    verification_status: PropertyRef = PropertyRef("VerificationStatus")
    bounce_topic: PropertyRef = PropertyRef("BounceTopic")
    complaint_topic: PropertyRef = PropertyRef("ComplaintTopic")
    delivery_topic: PropertyRef = PropertyRef("DeliveryTopic")
    forwarding_enabled: PropertyRef = PropertyRef("ForwardingEnabled")
    headers_in_bounce_notifications_enabled: PropertyRef = PropertyRef(
        "HeadersInBounceNotificationsEnabled"
    )
    headers_in_complaint_notifications_enabled: PropertyRef = PropertyRef(
        "HeadersInComplaintNotificationsEnabled"
    )
    headers_in_delivery_notifications_enabled: PropertyRef = PropertyRef(
        "HeadersInDeliveryNotificationsEnabled"
    )
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SESIdentityToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SESIdentityToAWSAccount(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SESIdentityToAwsAccountRelProperties = (
        SESIdentityToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class SESIdentitySchema(CartographyNodeSchema):
    label: str = "SESIdentity"
    properties: SESIdentityNodeProperties = SESIdentityNodeProperties()
    sub_resource_relationship: SESIdentityToAWSAccount = SESIdentityToAWSAccount()
