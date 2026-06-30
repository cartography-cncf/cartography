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
class ScalewayKapsuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    provider_id: PropertyRef = PropertyRef("provider_id")
    public_ip_v4: PropertyRef = PropertyRef("public_ip_v4")
    public_ip_v6: PropertyRef = PropertyRef("public_ip_v6")
    error_message: PropertyRef = PropertyRef("error_message")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayKapsuleNodeToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayKapsuleNode)
class ScalewayKapsuleNodeToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayKapsuleNodeToProjectRelProperties = (
        ScalewayKapsuleNodeToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayKapsuleNodeToPoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayKapsulePool)-[:HAS]->(:ScalewayKapsuleNode)
class ScalewayKapsuleNodeToPoolRel(CartographyRelSchema):
    target_node_label: str = "ScalewayKapsulePool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("pool_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayKapsuleNodeToPoolRelProperties = (
        ScalewayKapsuleNodeToPoolRelProperties()
    )


@dataclass(frozen=True)
class ScalewayKapsuleNodeToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayKapsuleCluster)-[:HAS]->(:ScalewayKapsuleNode)
class ScalewayKapsuleNodeToClusterRel(CartographyRelSchema):
    target_node_label: str = "ScalewayKapsuleCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cluster_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayKapsuleNodeToClusterRelProperties = (
        ScalewayKapsuleNodeToClusterRelProperties()
    )


@dataclass(frozen=True)
class ScalewayKapsuleNodeSchema(CartographyNodeSchema):
    label: str = "ScalewayKapsuleNode"
    properties: ScalewayKapsuleNodeProperties = ScalewayKapsuleNodeProperties()
    sub_resource_relationship: ScalewayKapsuleNodeToProjectRel = (
        ScalewayKapsuleNodeToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayKapsuleNodeToPoolRel(),
            ScalewayKapsuleNodeToClusterRel(),
        ]
    )
