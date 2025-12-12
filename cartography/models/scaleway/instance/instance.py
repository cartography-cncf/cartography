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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    tags: PropertyRef = PropertyRef("tags")
    commercial_type: PropertyRef = PropertyRef("commercial_type")
    creation_date: PropertyRef = PropertyRef("creation_date")
    dynamic_ip_required: PropertyRef = PropertyRef("dynamic_ip_required")
    routed_ip_enabled: PropertyRef = PropertyRef("routed_ip_enabled")
    enable_ipv6: PropertyRef = PropertyRef("enable_ipv6")
    hostname: PropertyRef = PropertyRef("hostname")
    private_ip: PropertyRef = PropertyRef("private_ip")
    mac_address: PropertyRef = PropertyRef("mac_address")
    modification_date: PropertyRef = PropertyRef("modification_date")
    state: PropertyRef = PropertyRef("state")
    location_cluster_id: PropertyRef = PropertyRef("location.cluster_id")
    location_hypervisor_id: PropertyRef = PropertyRef("location.hypervisor_id")
    location_node_id: PropertyRef = PropertyRef("location.node_id")
    location_platform_id: PropertyRef = PropertyRef("location.platform_id")
    ipv6_address: PropertyRef = PropertyRef("ipv6.address")
    ipv6_gateway: PropertyRef = PropertyRef("ipv6.gateway")
    ipv6_netmask: PropertyRef = PropertyRef("ipv6.netmask")
    boot_type: PropertyRef = PropertyRef("boot_type")
    state_detail: PropertyRef = PropertyRef("state_detail")
    arch: PropertyRef = PropertyRef("arch")
    private_nics: PropertyRef = PropertyRef("private_nics")
    zone: PropertyRef = PropertyRef("zone")
    end_of_service: PropertyRef = PropertyRef("end_of_service")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayInstanceToVolumeProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayVolume)<-[:MOUNTS]-(:ScalewayInstance)
class ScalewayInstanceToVolumeRel(CartographyRelSchema):
    target_node_label: str = "ScalewayVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("volumes_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MOUNTS"
    properties: ScalewayInstanceToVolumeProperties = (
        ScalewayInstanceToVolumeProperties()
    )


@dataclass(frozen=True)
class ScalewayInstanceToFlexibleIpProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayFlexibleIp)-[:IDENTIFIES]->(:ScalewayInstance)
class ScalewayInstanceToFlexibleIpRel(CartographyRelSchema):
    target_node_label: str = "ScalewayFlexibleIp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("public_ips", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTIFIES"
    properties: ScalewayInstanceToFlexibleIpProperties = (
        ScalewayInstanceToFlexibleIpProperties()
    )


# TODO: Link to Image with image.id
# TODO: Link to SecurityGroup with security_group.id
# TODO: Link to PlacementGroup with placement_group.id


@dataclass(frozen=True)
class ScalewayInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayInstance)
class ScalewayInstanceToProjectRel(CartographyRelSchema):
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
    label: str = "ScalewayInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeInstance"])
    properties: ScalewayInstanceProperties = ScalewayInstanceProperties()
    sub_resource_relationship: ScalewayInstanceToProjectRel = (
        ScalewayInstanceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayInstanceToVolumeRel(),
        ]
    )
