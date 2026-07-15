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
class ScalewayKapsulePoolProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Pool UUID.")
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Pool name.")
    status: PropertyRef = PropertyRef("status", description="Pool status.")
    version: PropertyRef = PropertyRef(
        "version", description="Kubernetes version of the pool."
    )
    node_type: PropertyRef = PropertyRef(
        "node_type",
        description="Scaleway instance commercial type used for nodes (e.g. `DEV1-M`).",
    )
    autoscaling: PropertyRef = PropertyRef(
        "autoscaling", description="True if the pool autoscales."
    )
    size: PropertyRef = PropertyRef("size", description="Current size of the pool.")
    min_size: PropertyRef = PropertyRef(
        "min_size", description="Minimum size for autoscaling."
    )
    max_size: PropertyRef = PropertyRef(
        "max_size", description="Maximum size for autoscaling."
    )
    container_runtime: PropertyRef = PropertyRef(
        "container_runtime", description="Container runtime (`containerd`, ...)."
    )
    autohealing: PropertyRef = PropertyRef(
        "autohealing", description="True if autohealing is enabled."
    )
    root_volume_type: PropertyRef = PropertyRef(
        "root_volume_type", description="Root volume type for nodes."
    )
    root_volume_size: PropertyRef = PropertyRef(
        "root_volume_size", description="Root volume size in bytes."
    )
    public_ip_disabled: PropertyRef = PropertyRef(
        "public_ip_disabled", description="True if nodes have no public IP."
    )
    placement_group_id: PropertyRef = PropertyRef(
        "placement_group_id", description="ID of the placement group, if any."
    )
    security_group_id: PropertyRef = PropertyRef(
        "security_group_id", description="Security group applied to the nodes."
    )
    tags: PropertyRef = PropertyRef("tags", description="Pool tags.")
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone the pool's nodes live in."
    )
    region: PropertyRef = PropertyRef("region", description="Region the pool lives in.")
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
class ScalewayKapsulePoolToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayKapsulePool)
class ScalewayKapsulePoolToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayKapsulePool` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayKapsulePoolToProjectRelProperties = (
        ScalewayKapsulePoolToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayKapsulePoolToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayKapsuleCluster)-[:HAS]->(:ScalewayKapsulePool)
class ScalewayKapsulePoolToClusterRel(CartographyRelSchema):
    """Connects `ScalewayKapsuleCluster` to `ScalewayKapsulePool` through `HAS`."""

    target_node_label: str = "ScalewayKapsuleCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cluster_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayKapsulePoolToClusterRelProperties = (
        ScalewayKapsulePoolToClusterRelProperties()
    )


@dataclass(frozen=True)
class ScalewayKapsulePoolSchema(CartographyNodeSchema):
    """Represents a Kapsule node pool: a homogeneous group of nodes provisioned for a
    Kapsule cluster.
    """

    label: str = "ScalewayKapsulePool"
    properties: ScalewayKapsulePoolProperties = ScalewayKapsulePoolProperties()
    sub_resource_relationship: ScalewayKapsulePoolToProjectRel = (
        ScalewayKapsulePoolToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayKapsulePoolToClusterRel(),
        ]
    )
