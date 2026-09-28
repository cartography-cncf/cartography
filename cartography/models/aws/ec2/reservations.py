from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_EC2_RESERVATION
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EC2ReservationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "ReservationId", description="The ID of the reservation (same as reservationid)"
    )
    reservationid: PropertyRef = PropertyRef(
        "ReservationId", description="The ID of the reservation."
    )
    ownerid: PropertyRef = PropertyRef(
        "OwnerId", description="The ID of the AWS account that owns the reservation."
    )
    requesterid: PropertyRef = PropertyRef(
        "RequesterId",
        description="The ID of the requester that launched the instances on your behalf",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2ReservationToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2ReservationToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2ReservationToAWSAccountRelRelProperties = (
        EC2ReservationToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2ReservationSchema(CartographyNodeSchema):
    """Representation of an AWS EC2 [Reservation](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Reservation.html)."""

    label: str = "AWSEC2Reservation"
    # DEPRECATED: legacy EC2Reservation node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_EC2_RESERVATION])
    properties: EC2ReservationNodeProperties = EC2ReservationNodeProperties()
    sub_resource_relationship: EC2ReservationToAWSAccountRel = (
        EC2ReservationToAWSAccountRel()
    )
