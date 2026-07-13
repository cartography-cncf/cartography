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
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    version: PropertyRef = PropertyRef("version")
    node_type: PropertyRef = PropertyRef("node_type")
    cluster_size: PropertyRef = PropertyRef("cluster_size")
    tls_enabled: PropertyRef = PropertyRef("tls_enabled")
    user_name: PropertyRef = PropertyRef("user_name")
    tags: PropertyRef = PropertyRef("tags")
    # Endpoint summary fields (flattened from the endpoints list).
    is_public: PropertyRef = PropertyRef("is_public")
    public_endpoint_ip: PropertyRef = PropertyRef("public_endpoint_ip")
    public_endpoint_port: PropertyRef = PropertyRef("public_endpoint_port")
    private_endpoint_ip: PropertyRef = PropertyRef("private_endpoint_ip")
    private_endpoint_port: PropertyRef = PropertyRef("private_endpoint_port")
    zone: PropertyRef = PropertyRef("zone")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayRedisClusterToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayRedisCluster)
class ScalewayRedisClusterToProjectRel(CartographyRelSchema):
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
