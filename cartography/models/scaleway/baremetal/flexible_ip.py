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
class ScalewayElasticMetalFlexibleIpProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    description: PropertyRef = PropertyRef("description")
    tags: PropertyRef = PropertyRef("tags")
    status: PropertyRef = PropertyRef("status")
    ip_address: PropertyRef = PropertyRef("ip_address")
    reverse: PropertyRef = PropertyRef("reverse")
    server_id: PropertyRef = PropertyRef("server_id")
    zone: PropertyRef = PropertyRef("zone")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayElasticMetalFlexibleIpToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayElasticMetalFlexibleIp)
class ScalewayElasticMetalFlexibleIpToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayElasticMetalFlexibleIpToProjectRelProperties = (
        ScalewayElasticMetalFlexibleIpToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayElasticMetalFlexibleIpToServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayElasticMetalFlexibleIp)-[:IDENTIFIES]->(:ScalewayElasticMetalServer)
class ScalewayElasticMetalFlexibleIpToServerRel(CartographyRelSchema):
    target_node_label: str = "ScalewayElasticMetalServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IDENTIFIES"
    properties: ScalewayElasticMetalFlexibleIpToServerRelProperties = (
        ScalewayElasticMetalFlexibleIpToServerRelProperties()
    )


@dataclass(frozen=True)
class ScalewayElasticMetalFlexibleIpSchema(CartographyNodeSchema):
    label: str = "ScalewayElasticMetalFlexibleIp"
    properties: ScalewayElasticMetalFlexibleIpProperties = (
        ScalewayElasticMetalFlexibleIpProperties()
    )
    sub_resource_relationship: ScalewayElasticMetalFlexibleIpToProjectRel = (
        ScalewayElasticMetalFlexibleIpToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayElasticMetalFlexibleIpToServerRel(),
        ]
    )
