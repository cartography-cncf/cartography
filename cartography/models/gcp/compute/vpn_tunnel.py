from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPVpnTunnelNodeProperties(CartographyNodeProperties):
    # NOTE: The GCP API returns `sharedSecret`/`sharedSecretHash` (the IKE
    # pre-shared key) on tunnel resources. These are deliberately NOT modeled
    # here so that Cartography never ingests VPN secrets.
    id: PropertyRef = PropertyRef(
        "partial_uri",
        extra_index=True,
        description="A partial resource URI representing this VPN Tunnel. Has the form `projects/{project}/regions/{region}/vpnTunnels/{tunnel name}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    self_link: PropertyRef = PropertyRef(
        "self_link",
        description="The full resource URI representing this VPN Tunnel. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of this VPN Tunnel."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this VPN Tunnel belongs to."
    )
    region: PropertyRef = PropertyRef(
        "region", description="The region of this VPN Tunnel."
    )
    description: PropertyRef = PropertyRef(
        "description", description="A description for this VPN Tunnel."
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="The status of the VPN tunnel, e.g. ESTABLISHED, WAITING_FOR_FULL_CONFIG, or FAILED.",
    )
    detailed_status: PropertyRef = PropertyRef(
        "detailed_status",
        description="A detailed human-readable status message for the VPN tunnel.",
    )
    peer_ip: PropertyRef = PropertyRef(
        "peer_ip",
        description="The IP address of the peer VPN gateway. Set for tunnels to non-GCP peers.",
    )
    ike_version: PropertyRef = PropertyRef(
        "ike_version",
        description="The IKE protocol version of the tunnel (1 or 2).",
    )
    local_traffic_selector: PropertyRef = PropertyRef(
        "local_traffic_selector",
        description="Local traffic selector CIDR ranges to use when establishing the VPN tunnel.",
    )
    remote_traffic_selector: PropertyRef = PropertyRef(
        "remote_traffic_selector",
        description="Remote traffic selector CIDR ranges to use when establishing the VPN tunnel.",
    )
    vpn_gateway_partial_uri: PropertyRef = PropertyRef(
        "vpn_gateway_partial_uri",
        description="The partial URI of the HA VPN gateway on the local side of this tunnel. Unset for classic VPN tunnels.",
    )
    peer_gcp_gateway_partial_uri: PropertyRef = PropertyRef(
        "peer_gcp_gateway_partial_uri",
        description="The partial URI of the peer HA VPN gateway, when the tunnel connects to another GCP VPN gateway. The peer gateway may belong to a different project.",
    )
    target_vpn_gateway_partial_uri: PropertyRef = PropertyRef(
        "target_vpn_gateway_partial_uri",
        description="The partial URI of the classic (legacy) target VPN gateway this tunnel is attached to, if any.",
    )
    router_partial_uri: PropertyRef = PropertyRef(
        "router_partial_uri",
        description="The partial URI of the Cloud Router associated with this tunnel, if any.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="The creation timestamp of this VPN Tunnel.",
    )


@dataclass(frozen=True)
class GCPVpnTunnelToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpnTunnelToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVpnTunnelToProjectRelProperties = (
        GCPVpnTunnelToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVpnTunnelToGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpnTunnelToGatewayRel(CartographyRelSchema):
    """Points from the VPN tunnel to the local HA VPN gateway it runs on."""

    target_node_label: str = "GCPVpnGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("vpn_gateway_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_GATEWAY"
    properties: GCPVpnTunnelToGatewayRelProperties = (
        GCPVpnTunnelToGatewayRelProperties()
    )


@dataclass(frozen=True)
class GCPVpnTunnelToPeerGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpnTunnelToPeerGatewayRel(CartographyRelSchema):
    """Points from the VPN tunnel to the peer HA VPN gateway on the remote side.
    The peer gateway may live in a different project; if that project has not been
    synced, the target is a stub GCPVpnGateway node holding only its partial URI."""

    target_node_label: str = "GCPVpnGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("peer_gcp_gateway_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO_GATEWAY"
    properties: GCPVpnTunnelToPeerGatewayRelProperties = (
        GCPVpnTunnelToPeerGatewayRelProperties()
    )


@dataclass(frozen=True)
class GCPVpnTunnelSchema(CartographyNodeSchema):
    """Representation of a GCP [Cloud VPN Tunnel](https://cloud.google.com/compute/docs/reference/rest/v1/vpnTunnels).
    Cartography never ingests the tunnel's `sharedSecret`/`sharedSecretHash` fields."""

    label: str = "GCPVpnTunnel"
    properties: GCPVpnTunnelNodeProperties = GCPVpnTunnelNodeProperties()
    sub_resource_relationship: GCPVpnTunnelToProjectRel = GCPVpnTunnelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPVpnTunnelToGatewayRel(),
            GCPVpnTunnelToPeerGatewayRel(),
        ]
    )
