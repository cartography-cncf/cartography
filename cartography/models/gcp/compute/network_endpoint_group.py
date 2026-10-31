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
class GCPNetworkEndpointGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri", description="Stable identifier for this resource."
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The name of the network endpoint group.",
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="Server-defined URL for the resource."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="The project ID that this network endpoint group belongs to.",
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="The zone of this network endpoint group, for zonal NEGs."
    )
    region: PropertyRef = PropertyRef(
        "region",
        description="The region of this network endpoint group, for regional NEGs.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="An optional description of this network endpoint group.",
    )
    network_endpoint_type: PropertyRef = PropertyRef(
        "network_endpoint_type",
        description="Type of the endpoints in this group (e.g., `GCE_VM_IP_PORT` for GKE container-native load balancing, `SERVERLESS`, `INTERNET_FQDN_PORT`).",
    )
    network: PropertyRef = PropertyRef(
        "network_partial_uri",
        description="The partial URI of the VPC network the endpoints belong to.",
    )
    subnetwork: PropertyRef = PropertyRef(
        "subnetwork_partial_uri",
        description="The partial URI of the subnet the endpoints belong to.",
    )
    default_port: PropertyRef = PropertyRef(
        "default_port",
        description="The port used when an endpoint does not specify one.",
    )
    size: PropertyRef = PropertyRef(
        "size", description="The number of network endpoints in the group."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp", description="Creation timestamp of the resource."
    )


@dataclass(frozen=True)
class GCPNetworkEndpointGroupToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPNetworkEndpointGroupToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPNetworkEndpointGroupToProjectRelProperties = (
        GCPNetworkEndpointGroupToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPNetworkEndpointGroupSchema(CartographyNodeSchema):
    """Representation of a GCP [Network Endpoint Group](https://cloud.google.com/compute/docs/reference/rest/v1/networkEndpointGroups). GKE creates zonal NEGs for Services annotated `cloud.google.com/neg`, which lets a load balancer built outside the cluster send traffic straight to pod IPs."""

    label: str = "GCPNetworkEndpointGroup"
    properties: GCPNetworkEndpointGroupNodeProperties = (
        GCPNetworkEndpointGroupNodeProperties()
    )
    sub_resource_relationship: GCPNetworkEndpointGroupToProjectRel = (
        GCPNetworkEndpointGroupToProjectRel()
    )
