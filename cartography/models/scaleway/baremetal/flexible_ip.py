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
    id: PropertyRef = PropertyRef("id", description="ID of the flexible IP.")
    description: PropertyRef = PropertyRef(
        "description", description="Description of the flexible IP."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags attached to the flexible IP."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Status of the flexible IP."
    )
    ip_address: PropertyRef = PropertyRef("ip_address", description="The IP address.")
    reverse: PropertyRef = PropertyRef("reverse", description="Reverse DNS value.")
    server_id: PropertyRef = PropertyRef(
        "server_id", description="ID of the server the IP is attached to."
    )
    zone: PropertyRef = PropertyRef("zone", description="Availability zone.")
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
class ScalewayElasticMetalFlexibleIpToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayElasticMetalFlexibleIp)
class ScalewayElasticMetalFlexibleIpToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayElasticMetalFlexibleIp` through `RESOURCE`."""

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
    """Connects `ScalewayElasticMetalFlexibleIp` to `ScalewayElasticMetalServer` through
    `IDENTIFIES`.
    """

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
    """Represents a flexible (portable) public IP for Elastic Metal servers in Scaleway."""

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
