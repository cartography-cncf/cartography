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
class ScalewayInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Instance unique ID.")
    name: PropertyRef = PropertyRef("name", description="Instance name.")
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the Instance."
    )
    commercial_type: PropertyRef = PropertyRef(
        "commercial_type", description="Instance commercial type (eg. GP1-M)."
    )
    creation_date: PropertyRef = PropertyRef(
        "creation_date", description="Instance creation date."
    )
    dynamic_ip_required: PropertyRef = PropertyRef(
        "dynamic_ip_required", description="True if a dynamic IPv4 is required."
    )
    routed_ip_enabled: PropertyRef = PropertyRef(
        "routed_ip_enabled",
        description="True to configure the instance so it uses the routed IP mode. Use of routed_ip_enabled as False is deprecated.",
    )
    enable_ipv6: PropertyRef = PropertyRef(
        "enable_ipv6",
        description="True if IPv6 is enabled (deprecated and always False when routed_ip_enabled is True).",
    )
    hostname: PropertyRef = PropertyRef("hostname", description="Instance host name.")
    private_ip: PropertyRef = PropertyRef(
        "private_ip",
        description="Private IP address of the Instance (deprecated and always null when routed_ip_enabled is True).",
    )
    # List of attached public IP ids (also used to match the FlexibleIp
    # relationship). Persisted so exposure rules can test for a public IP.
    public_ips: PropertyRef = PropertyRef(
        "public_ips", description="Public IP addresses assigned to the instance."
    )
    mac_address: PropertyRef = PropertyRef(
        "mac_address", description="The server's MAC address."
    )
    modification_date: PropertyRef = PropertyRef(
        "modification_date", description="Instance modification date."
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Instance state (`running`, `stopped`, `stopped in place`, `starting`, `stopping`, `locked`)",
    )
    location_cluster_id: PropertyRef = PropertyRef(
        "location.cluster_id", description="Instance location, cluster ID"
    )
    location_hypervisor_id: PropertyRef = PropertyRef(
        "location.hypervisor_id", description="Instance locationm, hypervisor ID"
    )
    location_node_id: PropertyRef = PropertyRef(
        "location.node_id", description="Instance location, node ID"
    )
    location_platform_id: PropertyRef = PropertyRef(
        "location.platform_id", description="Instance location, plateform ID"
    )
    ipv6_address: PropertyRef = PropertyRef(
        "ipv6.address", description="Instance IPv6 IP-Address."
    )
    ipv6_gateway: PropertyRef = PropertyRef(
        "ipv6.gateway", description="IPv6 IP-addresses gateway."
    )
    ipv6_netmask: PropertyRef = PropertyRef(
        "ipv6.netmask", description="IPv6 IP-addresses CIDR netmask."
    )
    boot_type: PropertyRef = PropertyRef(
        "boot_type", description="Instance boot type (`local`, `bootscript`, `rescue`)"
    )
    state_detail: PropertyRef = PropertyRef(
        "state_detail", description="Detailed information about the Instance state."
    )
    arch: PropertyRef = PropertyRef(
        "arch",
        description="Instance architecture (`unknown_arch`, `x86_64`, `arm`, `arm64`)",
    )
    private_nics: PropertyRef = PropertyRef(
        "private_nics", description="Instance private NICs."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone in which the Instance is located."
    )
    end_of_service: PropertyRef = PropertyRef(
        "end_of_service",
        description="True if the Instance type has reached end of service.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayInstanceToVolumeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayVolume)<-[:MOUNTS]-(:ScalewayInstance)
class ScalewayInstanceToVolumeRel(CartographyRelSchema):
    """Connects `ScalewayInstance` to `ScalewayVolume` through `MOUNTS`."""

    target_node_label: str = "ScalewayVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("volumes_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MOUNTS"
    properties: ScalewayInstanceToVolumeRelProperties = (
        ScalewayInstanceToVolumeRelProperties()
    )


@dataclass(frozen=True)
class ScalewayInstanceToFlexibleIpRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayFlexibleIp)-[:IDENTIFIES]->(:ScalewayInstance)
class ScalewayInstanceToFlexibleIpRel(CartographyRelSchema):
    """Connects `ScalewayFlexibleIp` to `ScalewayInstance` through `IDENTIFIES`."""

    target_node_label: str = "ScalewayFlexibleIp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("public_ips", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTIFIES"
    properties: ScalewayInstanceToFlexibleIpRelProperties = (
        ScalewayInstanceToFlexibleIpRelProperties()
    )


# Note: the (:ScalewayInstance)-[:MEMBER_OF_SCALEWAY_SECURITY_GROUP]->(:ScalewaySecurityGroup)
# edge is declared on the SecurityGroup side (see models/scaleway/instance/securitygroup.py).
# TODO: Link to Image with image.id
# TODO: Link to PlacementGroup with placement_group.id


@dataclass(frozen=True)
class ScalewayInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayInstance)
class ScalewayInstanceToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayInstance` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayInstanceToProjectRelProperties = (
        ScalewayInstanceToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayInstanceSchema(CartographyNodeSchema):
    """An Instance is a virtual computing unit that provides resources, such as processing
    power, memory, and network connectivity, to run your applications.
    """

    label: str = "ScalewayInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: ScalewayInstanceProperties = ScalewayInstanceProperties()
    sub_resource_relationship: ScalewayInstanceToProjectRel = (
        ScalewayInstanceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayInstanceToVolumeRel(),
            ScalewayInstanceToFlexibleIpRel(),
        ]
    )
