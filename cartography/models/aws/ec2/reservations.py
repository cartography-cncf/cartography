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
class EC2ReservationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ReservationId")
    reservationid: PropertyRef = PropertyRef("ReservationId")
    ownerid: PropertyRef = PropertyRef("OwnerId")
    requesterid: PropertyRef = PropertyRef("RequesterId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
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
    label: str = "EC2Reservation"
    properties: EC2ReservationNodeProperties = EC2ReservationNodeProperties()
    sub_resource_relationship: EC2ReservationToAWSAccountRel = (
        EC2ReservationToAWSAccountRel()
    )
