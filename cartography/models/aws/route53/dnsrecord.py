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
class AWSDNSRecordNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for this `AWSDNSRecord` node."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of this `AWSDNSRecord` node."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Type of this `AWSDNSRecord` node."
    )
    value: PropertyRef = PropertyRef(
        "value", description="DNS record value returned for the record name and type."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSDNSRecord` node.",
    )


@dataclass(frozen=True)
class AWSDNSRecordToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToZoneRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_DNS_ZONE` relationship from `AWSDNSRecord` to `AWSDNSZone`."

    target_node_label: str = "AWSDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"zoneid": PropertyRef("zoneid")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_DNS_ZONE"
    properties: AWSDNSRecordToZoneRelProperties = AWSDNSRecordToZoneRelProperties()


@dataclass(frozen=True)
class AWSDNSRecordToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSDNSRecord`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSDNSRecordToAWSAccountRelProperties = (
        AWSDNSRecordToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSDNSRecordToNameServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToNameServerRel(CartographyRelSchema):
    "Represents a `DNS_POINTS_TO` relationship from `AWSDNSRecord` to `AWSNameServer`."

    target_node_label: str = "AWSNameServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("servers", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: AWSDNSRecordToNameServerRelProperties = (
        AWSDNSRecordToNameServerRelProperties()
    )


@dataclass(frozen=True)
class AWSDNSRecordToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToEC2InstanceRel(CartographyRelSchema):
    "Represents a `DNS_POINTS_TO` relationship from `AWSDNSRecord` to `AWSEC2Instance`."

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "publicdnsname": PropertyRef("value"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: AWSDNSRecordToEC2InstanceRelProperties = (
        AWSDNSRecordToEC2InstanceRelProperties()
    )


@dataclass(frozen=True)
class AWSDNSRecordToLoadBalancerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToLoadBalancerRel(CartographyRelSchema):
    "Represents a `DNS_POINTS_TO` relationship from `AWSDNSRecord` to `AWSLoadBalancer`."

    target_node_label: str = "AWSLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "dnsname": PropertyRef("value"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: AWSDNSRecordToLoadBalancerRelProperties = (
        AWSDNSRecordToLoadBalancerRelProperties()
    )


@dataclass(frozen=True)
class AWSDNSRecordToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToLoadBalancerV2Rel(CartographyRelSchema):
    "Represents a `DNS_POINTS_TO` relationship from `AWSDNSRecord` to `AWSLoadBalancerV2`."

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "dnsname": PropertyRef("value"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: AWSDNSRecordToLoadBalancerV2RelProperties = (
        AWSDNSRecordToLoadBalancerV2RelProperties()
    )


@dataclass(frozen=True)
class AWSDNSRecordToESDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToESDomainRel(CartographyRelSchema):
    "Represents a `DNS_POINTS_TO` relationship from `AWSDNSRecord` to `AWSESDomain`."

    target_node_label: str = "AWSESDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "endpoint": PropertyRef("value"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: AWSDNSRecordToESDomainRelProperties = (
        AWSDNSRecordToESDomainRelProperties()
    )


@dataclass(frozen=True)
class AWSDNSRecordToDNSRecordRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToDNSRecordRel(CartographyRelSchema):
    "Represents a `DNS_POINTS_TO` relationship from `AWSDNSRecord` to `AWSDNSRecord`."

    target_node_label: str = "AWSDNSRecord"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("value"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: AWSDNSRecordToDNSRecordRelProperties = (
        AWSDNSRecordToDNSRecordRelProperties()
    )


@dataclass(frozen=True)
class AWSDNSRecordToIpRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToIpRel(CartographyRelSchema):
    "Represents a `DNS_POINTS_TO` relationship from `AWSDNSRecord` to `Ip`."

    target_node_label: str = "Ip"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("ip_addresses", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: AWSDNSRecordToIpRelProperties = AWSDNSRecordToIpRelProperties()


@dataclass(frozen=True)
class AWSDNSRecordToElasticIPAddressRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSDNSRecordToElasticIPAddressRel(CartographyRelSchema):
    "Represents a `DNS_POINTS_TO` relationship from `AWSDNSRecord` to `AWSElasticIPAddress`."

    target_node_label: str = "AWSElasticIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "public_ip": PropertyRef("value"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DNS_POINTS_TO"
    properties: AWSDNSRecordToElasticIPAddressRelProperties = (
        AWSDNSRecordToElasticIPAddressRelProperties()
    )


class AWSDNSRecordSchema(CartographyNodeSchema):
    "Represents an `AWSDNSRecord` node in the AWS graph."

    label: str = "AWSDNSRecord"
    properties: AWSDNSRecordNodeProperties = AWSDNSRecordNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DNSRecord"])
    sub_resource_relationship: AWSDNSRecordToAWSAccountRel = (
        AWSDNSRecordToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSDNSRecordToNameServerRel(),
            AWSDNSRecordToEC2InstanceRel(),
            AWSDNSRecordToLoadBalancerRel(),
            AWSDNSRecordToLoadBalancerV2Rel(),
            AWSDNSRecordToESDomainRel(),
            AWSDNSRecordToDNSRecordRel(),
            AWSDNSRecordToZoneRel(),
            AWSDNSRecordToIpRel(),
            AWSDNSRecordToElasticIPAddressRel(),
        ]
    )
