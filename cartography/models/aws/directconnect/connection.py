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
class DirectConnectConnectionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "connectionId", description="The ID of the Direct Connect connection"
    )
    connection_id: PropertyRef = PropertyRef(
        "connectionId", extra_index=True, description="The ID of the connection"
    )
    name: PropertyRef = PropertyRef(
        "connectionName", description="The name of the connection"
    )
    state: PropertyRef = PropertyRef(
        "connectionState",
        description=(
            "The state of the connection. Valid values: ordering, requested, pending, "
            "available, down, deleting, deleted, rejected, unknown"
        ),
    )
    owner_account: PropertyRef = PropertyRef(
        "ownerAccount", description="The AWS account that owns the connection"
    )
    bandwidth: PropertyRef = PropertyRef(
        "bandwidth", description="The bandwidth of the connection, e.g. 1Gbps or 50Mbps"
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="The location of the connection: the Direct Connect point of presence",
    )
    partner_name: PropertyRef = PropertyRef(
        "partnerName",
        description="The name of the service provider associated with the connection",
    )
    provider_name: PropertyRef = PropertyRef(
        "providerName",
        description="The name of the service provider associated with the connection",
    )
    vlan: PropertyRef = PropertyRef("vlan", description="The VLAN ID")
    lag_id: PropertyRef = PropertyRef(
        "lagId",
        description="The ID of the link aggregation group (LAG), when the connection is in one",
    )
    jumbo_frame_capable: PropertyRef = PropertyRef(
        "jumboFrameCapable", description="Indicates whether jumbo frames are supported"
    )
    has_logical_redundancy: PropertyRef = PropertyRef(
        "hasLogicalRedundancy",
        description="Indicates whether the connection supports a secondary BGP peer in the same address family",
    )
    mac_sec_capable: PropertyRef = PropertyRef(
        "macSecCapable",
        description="Indicates whether the connection supports MAC Security (MACsec)",
    )
    encryption_mode: PropertyRef = PropertyRef(
        "encryptionMode",
        description="The MACsec encryption mode. Valid values: no_encrypt, should_encrypt, must_encrypt",
    )
    port_encryption_status: PropertyRef = PropertyRef(
        "portEncryptionStatus", description="The MACsec port link status"
    )
    aws_device: PropertyRef = PropertyRef(
        "awsDeviceV2",
        description="The Direct Connect endpoint that terminates the physical connection",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the connection"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DirectConnectConnectionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DirectConnectConnectionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DirectConnectConnectionToAWSAccountRelProperties = (
        DirectConnectConnectionToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DirectConnectConnectionSchema(CartographyNodeSchema):
    """Representation of an AWS [Direct Connect connection](https://docs.aws.amazon.com/directconnect/latest/APIReference/API_Connection.html): the physical cross-connect between the customer network and AWS."""

    label: str = "AWSDirectConnectConnection"
    properties: DirectConnectConnectionNodeProperties = (
        DirectConnectConnectionNodeProperties()
    )
    sub_resource_relationship: DirectConnectConnectionToAWSAccountRel = (
        DirectConnectConnectionToAWSAccountRel()
    )
