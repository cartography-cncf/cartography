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
class ScalewayRedisClusterProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Cluster UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Cluster name."
    )
    status: PropertyRef = PropertyRef("status", description="Cluster status.")
    version: PropertyRef = PropertyRef(
        "version", description="Redis version (e.g. `7.0.5`)."
    )
    node_type: PropertyRef = PropertyRef(
        "node_type", description="Commercial node type."
    )
    cluster_size: PropertyRef = PropertyRef(
        "cluster_size", description="Number of nodes in the cluster."
    )
    tls_enabled: PropertyRef = PropertyRef(
        "tls_enabled", description="True if TLS is enabled for client traffic."
    )
    user_name: PropertyRef = PropertyRef("user_name", description="Default admin user.")
    tags: PropertyRef = PropertyRef("tags", description="Cluster tags.")
    # Endpoint summary fields (flattened from the endpoints list).
    is_public: PropertyRef = PropertyRef(
        "is_public",
        description="True if the cluster exposes a publicly reachable endpoint.",
    )
    public_endpoint_ip: PropertyRef = PropertyRef(
        "public_endpoint_ip", description="IP of the public endpoint, if any."
    )
    public_endpoint_port: PropertyRef = PropertyRef(
        "public_endpoint_port", description="Port of the public endpoint, if any."
    )
    private_endpoint_ip: PropertyRef = PropertyRef(
        "private_endpoint_ip",
        description="IP of the first private-network endpoint, if any.",
    )
    private_endpoint_port: PropertyRef = PropertyRef(
        "private_endpoint_port",
        description="Port of the first private-network endpoint, if any.",
    )
    zone: PropertyRef = PropertyRef("zone", description="Zone the cluster lives in.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )


@dataclass(frozen=True)
class ScalewayRedisClusterToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayRedisCluster)
class ScalewayRedisClusterToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayRedisCluster` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayRedisClusterToProjectRelProperties = (
        ScalewayRedisClusterToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayRedisClusterToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayRedisCluster)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
class ScalewayRedisClusterToPrivateNetworkRel(CartographyRelSchema):
    """Connects `ScalewayRedisCluster` to `ScalewayPrivateNetwork` through `ATTACHED_TO`."""

    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayRedisClusterToPrivateNetworkRelProperties = (
        ScalewayRedisClusterToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayRedisClusterSchema(CartographyNodeSchema):
    """Represents a managed Redis cluster (Scaleway "Managed Database for Redis")."""

    label: str = "ScalewayRedisCluster"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: ScalewayRedisClusterProperties = ScalewayRedisClusterProperties()
    sub_resource_relationship: ScalewayRedisClusterToProjectRel = (
        ScalewayRedisClusterToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayRedisClusterToPrivateNetworkRel(),
        ]
    )
