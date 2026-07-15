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
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Cluster UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Cluster name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Cluster description."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Cluster status (`ready`, `creating`, ...)."
    )
    type: PropertyRef = PropertyRef(
        "type_", description="Cluster offer type (e.g. `kapsule`, `multicloud`)."
    )
    version: PropertyRef = PropertyRef("version", description="Kubernetes version.")
    cni: PropertyRef = PropertyRef(
        "cni", description="CNI plugin (`cilium`, `calico`, ...)."
    )
    cluster_url: PropertyRef = PropertyRef("cluster_url", description="API server URL.")
    dns_wildcard: PropertyRef = PropertyRef(
        "dns_wildcard", description="Wildcard DNS name pointing at the cluster."
    )
    upgrade_available: PropertyRef = PropertyRef(
        "upgrade_available",
        description="True if a newer Kubernetes version is offered.",
    )
    pod_cidr: PropertyRef = PropertyRef("pod_cidr", description="Pod IP range.")
    service_cidr: PropertyRef = PropertyRef(
        "service_cidr", description="Service IP range."
    )
    service_dns_ip: PropertyRef = PropertyRef(
        "service_dns_ip", description="In-cluster DNS service IP."
    )
    private_network_id: PropertyRef = PropertyRef(
        "private_network_id",
        description="ID of the VPC private network this cluster is attached to (if any).",
    )
    apiserver_cert_sans: PropertyRef = PropertyRef(
        "apiserver_cert_sans", description="Extra SANs added to the apiserver cert."
    )
    feature_gates: PropertyRef = PropertyRef(
        "feature_gates", description="List of enabled Kubernetes feature gates."
    )
    admission_plugins: PropertyRef = PropertyRef(
        "admission_plugins", description="List of enabled admission plugins."
    )
    tags: PropertyRef = PropertyRef("tags", description="Cluster tags.")
    region: PropertyRef = PropertyRef(
        "region", description="Region the cluster lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayKapsuleClusterToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayKapsuleCluster)
class ScalewayKapsuleClusterToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayKapsuleCluster` through `RESOURCE`."""

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
    """Connects `ScalewayKapsuleCluster` to `ScalewayPrivateNetwork` through `ATTACHED_TO`."""

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
    """Represents a Scaleway Kapsule (managed Kubernetes) cluster."""

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
