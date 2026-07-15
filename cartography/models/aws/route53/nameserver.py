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
class NameServerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The address of the nameserver")
    name: PropertyRef = PropertyRef(
        "id", extra_index=True, description="The name or address of the nameserver"
    )
    zoneid: PropertyRef = PropertyRef(
        "zoneid",
        description="The ID of the Route53 hosted zone this name server belongs to",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class NameServerToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NameServerToZoneRel(CartographyRelSchema):
    "Represents a `NAMESERVER` relationship from `AWSDNSZone` to `AWSNameServer`."

    target_node_label: str = "AWSDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"zoneid": PropertyRef("zoneid")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NAMESERVER"
    properties: NameServerToZoneRelProperties = NameServerToZoneRelProperties()


@dataclass(frozen=True)
class NameServerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class NameServerToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSNameServer`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NameServerToAWSAccountRelProperties = (
        NameServerToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class NameServerSchema(CartographyNodeSchema):
    "Represents an `AWSNameServer` node in the AWS graph."

    label: str = "AWSNameServer"
    # DEPRECATED: legacy NameServer node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["NameServer"])
    properties: NameServerNodeProperties = NameServerNodeProperties()
    sub_resource_relationship: NameServerToAWSAccountRel = NameServerToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [NameServerToZoneRel()]
    )
