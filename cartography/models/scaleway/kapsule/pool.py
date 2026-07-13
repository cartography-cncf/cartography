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
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    version: PropertyRef = PropertyRef("version")
    node_type: PropertyRef = PropertyRef("node_type")
    autoscaling: PropertyRef = PropertyRef("autoscaling")
    size: PropertyRef = PropertyRef("size")
    min_size: PropertyRef = PropertyRef("min_size")
    max_size: PropertyRef = PropertyRef("max_size")
    container_runtime: PropertyRef = PropertyRef("container_runtime")
    autohealing: PropertyRef = PropertyRef("autohealing")
    root_volume_type: PropertyRef = PropertyRef("root_volume_type")
    root_volume_size: PropertyRef = PropertyRef("root_volume_size")
    public_ip_disabled: PropertyRef = PropertyRef("public_ip_disabled")
    placement_group_id: PropertyRef = PropertyRef("placement_group_id")
    security_group_id: PropertyRef = PropertyRef("security_group_id")
    tags: PropertyRef = PropertyRef("tags")
    zone: PropertyRef = PropertyRef("zone")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayKapsulePoolToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayKapsulePool)
class ScalewayKapsulePoolToProjectRel(CartographyRelSchema):
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
