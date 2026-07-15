from dataclasses import dataclass

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
class AWSDNSZoneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "zoneid", description="Unique identifier for this `AWSDNSZone` node."
    )
    zoneid: PropertyRef = PropertyRef(
        "zoneid",
        description="Identifier of the zoneid linked to this `AWSDNSZone` node.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of this `AWSDNSZone` node."
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Comment attached to the Route 53 hosted zone."
    )
    privatezone: PropertyRef = PropertyRef(
        "privatezone",
        description="Whether the hosted zone is private and associated with one or more VPCs.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSDNSZone` node.",
    )


@dataclass(frozen=True)
class AWSDNSZoneToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSZoneToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSDNSZone`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSDNSZoneToAWSAccountRelProperties = (
        AWSDNSZoneToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSDNSZoneSchema(CartographyNodeSchema):
    "Represents an `AWSDNSZone` node in the AWS graph."

    label: str = "AWSDNSZone"
    properties: AWSDNSZoneNodeProperties = AWSDNSZoneNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSZone"])
    sub_resource_relationship: AWSDNSZoneToAWSAccountRel = AWSDNSZoneToAWSAccountRel()
