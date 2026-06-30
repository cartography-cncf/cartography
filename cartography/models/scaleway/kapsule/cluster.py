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
class ScalewayKapsuleClusterProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    status: PropertyRef = PropertyRef("status")
    type: PropertyRef = PropertyRef("type_")
    version: PropertyRef = PropertyRef("version")
    cni: PropertyRef = PropertyRef("cni")
    cluster_url: PropertyRef = PropertyRef("cluster_url")
    dns_wildcard: PropertyRef = PropertyRef("dns_wildcard")
    upgrade_available: PropertyRef = PropertyRef("upgrade_available")
    pod_cidr: PropertyRef = PropertyRef("pod_cidr")
    service_cidr: PropertyRef = PropertyRef("service_cidr")
    service_dns_ip: PropertyRef = PropertyRef("service_dns_ip")
    private_network_id: PropertyRef = PropertyRef("private_network_id")
    apiserver_cert_sans: PropertyRef = PropertyRef("apiserver_cert_sans")
    feature_gates: PropertyRef = PropertyRef("feature_gates")
    admission_plugins: PropertyRef = PropertyRef("admission_plugins")
    tags: PropertyRef = PropertyRef("tags")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayKapsuleClusterToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayKapsuleCluster)
class ScalewayKapsuleClusterToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayKapsuleClusterToProjectRelProperties = (
        ScalewayKapsuleClusterToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayKapsuleClusterToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayKapsuleCluster)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
class ScalewayKapsuleClusterToPrivateNetworkRel(CartographyRelSchema):
    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayKapsuleClusterToPrivateNetworkRelProperties = (
        ScalewayKapsuleClusterToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayKapsuleClusterSchema(CartographyNodeSchema):
    label: str = "ScalewayKapsuleCluster"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeCluster"])
    properties: ScalewayKapsuleClusterProperties = ScalewayKapsuleClusterProperties()
    sub_resource_relationship: ScalewayKapsuleClusterToProjectRel = (
        ScalewayKapsuleClusterToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayKapsuleClusterToPrivateNetworkRel(),
        ]
    )
