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
class GCPVpnGatewayStubNodeProperties(CartographyNodeProperties):
    """
    Minimal properties for GCPVpnGateway stub nodes.
    These are created from VPN tunnel `peerGcpGateway` references so that
    CONNECTS_TO_GATEWAY relationships can be established even when the peer
    gateway's project is not synced.
    """

    id: PropertyRef = PropertyRef(
        "partial_uri",
        description="A partial resource URI representing this HA VPN Gateway. Has the form `projects/{project}/regions/{region}/vpnGateways/{gateway name}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    partial_uri: PropertyRef = PropertyRef(
        "partial_uri", extra_index=True, description="Same as `id`."
    )
    # NOTE: descriptions for properties shared with GCPVpnGatewaySchema must
    # match it exactly; the schema-docs generator rejects conflicting
    # descriptions for the same (label, property) pair.
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="The project ID that this VPN Gateway belongs to.",
    )


@dataclass(frozen=True)
class GCPVpnGatewayStubToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpnGatewayStubToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    # Matched on the peer project parsed from the stub's own partial URI (data
    # field), not on the PROJECT_ID kwarg of the syncing project: the stub
    # represents a gateway owned by the *peer* project.
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVpnGatewayStubToProjectRelProperties = (
        GCPVpnGatewayStubToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVpnGatewayStubSchema(CartographyNodeSchema):
    """Representation of a GCP [HA VPN Gateway](https://cloud.google.com/compute/docs/reference/rest/v1/vpnGateways)
    placeholder for gateways whose owning project has not been synced."""

    label: str = "GCPVpnGateway"
    properties: GCPVpnGatewayStubNodeProperties = GCPVpnGatewayStubNodeProperties()
    # No extra fields are set on purpose: a later full sync of the owning project
    # MERGEs on the same id and fills in the complete gateway properties.
    sub_resource_relationship: GCPVpnGatewayStubToProjectRel = (
        GCPVpnGatewayStubToProjectRel()
    )
