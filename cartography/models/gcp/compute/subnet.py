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
class GCPSubnetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "partial_uri",
        extra_index=True,
        description="A partial resource URI representing this Subnet.  Has the form `projects/{project}/regions/{region}/subnetworks/{subnet name}`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    partial_uri: PropertyRef = PropertyRef("partial_uri", description="Same as `id`.")
    self_link: PropertyRef = PropertyRef(
        "self_link",
        description="The full resource URI representing this subnet. Has the form `https://www.googleapis.com/compute/v1/{partial_uri}`.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The name of this Subnet."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The project ID that this Subnet belongs to."
    )
    region: PropertyRef = PropertyRef(
        "region", description="The region of this Subnet."
    )
    gateway_address: PropertyRef = PropertyRef(
        "gateway_address", description="Gateway IP address of this Subnet."
    )
    ip_cidr_range: PropertyRef = PropertyRef(
        "ip_cidr_range", description="The CIDR range covered by this Subnet."
    )
    private_ip_google_access: PropertyRef = PropertyRef(
        "private_ip_google_access",
        description="Whether the VMs in this subnet can access Google services without assigned external IP addresses. This field can be both set at resource creation time and updated using setPrivateIpGoogleAccess.",
    )
    flow_logs_enabled: PropertyRef = PropertyRef(
        "flow_logs_enabled",
        description="Whether VPC Flow Logs are enabled for the subnet.",
    )
    flow_logs_aggregation_interval: PropertyRef = PropertyRef(
        "flow_logs_aggregation_interval",
        description="Flow Logs aggregation interval, e.g. `INTERVAL_5_SEC`.",
    )
    flow_logs_sampling: PropertyRef = PropertyRef(
        "flow_logs_sampling",
        description="Flow Logs sampling rate, e.g. `1.0` for 100%.",
    )
    flow_logs_metadata: PropertyRef = PropertyRef(
        "flow_logs_metadata",
        description="Flow Logs metadata mode, e.g. `INCLUDE_ALL_METADATA`.",
    )
    flow_logs_filter_expr: PropertyRef = PropertyRef(
        "flow_logs_filter_expr",
        description="Optional Flow Logs filter expression when subnet logging is filtered.",
    )
    purpose: PropertyRef = PropertyRef(
        "purpose",
        description="Purpose of the subnet, e.g. `PRIVATE` or service-specific values such as internal load-balancer reservations.",
    )
    vpc_partial_uri: PropertyRef = PropertyRef(
        "vpc_partial_uri",
        description="The partial URI of the VPC that this Subnet is a part of.",
    )


@dataclass(frozen=True)
class GCPSubnetToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPSubnetToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPSubnetToProjectRelProperties = GCPSubnetToProjectRelProperties()


@dataclass(frozen=True)
class GCPSubnetToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPSubnetToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("vpc_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: GCPSubnetToVpcRelProperties = GCPSubnetToVpcRelProperties()


@dataclass(frozen=True)
class GCPSubnetSchema(CartographyNodeSchema):
    """Representation of a GCP [Subnetwork](https://cloud.google.com/compute/docs/reference/rest/v1/subnetworks)."""

    label: str = "GCPSubnet"
    properties: GCPSubnetNodeProperties = GCPSubnetNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Subnet"])
    sub_resource_relationship: GCPSubnetToProjectRel = GCPSubnetToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPSubnetToVpcRel(),
        ]
    )
