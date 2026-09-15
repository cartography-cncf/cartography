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
class GCPVpcPeeringNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="A constructed unique ID for this VPC peering of the form `projects/{project}/global/networks/{network name}/networkPeerings/{peering name}`. "
        "The GCP API does not expose a resource URI for peerings, so Cartography derives one from the local network and peering name.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The name of this VPC Network Peering connection.",
    )
    project_id: PropertyRef = PropertyRef(
        "PROJECT_ID",
        set_in_kwargs=True,
        description="The project ID of the local side of this peering (the project whose network the peering is configured on).",
    )
    network_partial_uri: PropertyRef = PropertyRef(
        "network_partial_uri",
        description="The partial URI of the local VPC network this peering is configured on, e.g. `projects/{project}/global/networks/{network name}`.",
    )
    peer_network_partial_uri: PropertyRef = PropertyRef(
        "peer_network_partial_uri",
        description="The partial URI of the peer VPC network, e.g. `projects/{peer project}/global/networks/{peer network name}`. The peer network may belong to a different project.",
    )
    peer_project_id: PropertyRef = PropertyRef(
        "peer_project_id",
        description="The project ID of the peer VPC network, parsed from the peer network URI.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="The peering state, either ACTIVE or INACTIVE. A peering becomes ACTIVE only when both sides are connected.",
    )
    state_details: PropertyRef = PropertyRef(
        "state_details",
        description="Additional details about the current peering state.",
    )
    peer_mtu: PropertyRef = PropertyRef(
        "peer_mtu",
        description="Maximum Transmission Unit in bytes of the peer network.",
    )
    stack_type: PropertyRef = PropertyRef(
        "stack_type",
        description="Which IP stack(s) are allowed to be used by the peering, e.g. IPV4_ONLY or IPV4_IPV6.",
    )
    update_strategy: PropertyRef = PropertyRef(
        "update_strategy",
        description="The update strategy of the peering, e.g. INDEPENDENT or CONSERVATIVE.",
    )
    auto_create_routes: PropertyRef = PropertyRef(
        "auto_create_routes",
        description="Whether to automatically create routes for the peer network's subnets.",
    )
    exchange_subnet_routes: PropertyRef = PropertyRef(
        "exchange_subnet_routes",
        description="Whether subnet routes are exchanged with the peer network.",
    )
    import_custom_routes: PropertyRef = PropertyRef(
        "import_custom_routes",
        description="Whether custom routes are imported from the peer network.",
    )
    export_custom_routes: PropertyRef = PropertyRef(
        "export_custom_routes",
        description="Whether custom routes are exported to the peer network.",
    )
    import_subnet_routes_with_public_ip: PropertyRef = PropertyRef(
        "import_subnet_routes_with_public_ip",
        description="Whether subnet routes with public IP ranges are imported from the peer network.",
    )
    export_subnet_routes_with_public_ip: PropertyRef = PropertyRef(
        "export_subnet_routes_with_public_ip",
        description="Whether subnet routes with public IP ranges are exported to the peer network.",
    )


@dataclass(frozen=True)
class GCPVpcPeeringToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpcPeeringToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVpcPeeringToProjectRelProperties = (
        GCPVpcPeeringToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPVpcPeeringToLocalVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpcPeeringToLocalVpcRel(CartographyRelSchema):
    """Points from the peering to the local VPC network it is configured on."""

    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("network_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LOCAL_NETWORK"
    properties: GCPVpcPeeringToLocalVpcRelProperties = (
        GCPVpcPeeringToLocalVpcRelProperties()
    )


@dataclass(frozen=True)
class GCPVpcPeeringToPeerVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpcPeeringToPeerVpcRel(CartographyRelSchema):
    """Points from the peering to the peer VPC network. The peer VPC may live in a
    different project; if that project has not been synced, the target is a stub
    GCPVpc node holding only its partial URI."""

    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("peer_network_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PEER_NETWORK"
    properties: GCPVpcPeeringToPeerVpcRelProperties = (
        GCPVpcPeeringToPeerVpcRelProperties()
    )


@dataclass(frozen=True)
class GCPVpcPeeringSchema(CartographyNodeSchema):
    """Representation of one side of a GCP [VPC Network Peering](https://cloud.google.com/vpc/docs/vpc-peering)
    connection. GCP reports each peering from each participating network's perspective, so Cartography
    creates one GCPVpcPeering node per side; the two sides are joined through their shared
    LOCAL_NETWORK / PEER_NETWORK edges to GCPVpc nodes, which may belong to different projects.
    """

    label: str = "GCPVpcPeering"
    properties: GCPVpcPeeringNodeProperties = GCPVpcPeeringNodeProperties()
    sub_resource_relationship: GCPVpcPeeringToProjectRel = GCPVpcPeeringToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPVpcPeeringToLocalVpcRel(),
            GCPVpcPeeringToPeerVpcRel(),
        ]
    )
