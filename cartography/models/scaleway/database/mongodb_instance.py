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
class ScalewayMongoDBInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    version: PropertyRef = PropertyRef("version")
    node_type: PropertyRef = PropertyRef("node_type")
    node_amount: PropertyRef = PropertyRef("node_amount")
    volume_type: PropertyRef = PropertyRef("volume_type")
    volume_size: PropertyRef = PropertyRef("volume_size")
    tags: PropertyRef = PropertyRef("tags")
    # Endpoint summary fields (flattened from the endpoints list).
    is_public: PropertyRef = PropertyRef("is_public")
    public_endpoint_dns: PropertyRef = PropertyRef("public_endpoint_dns")
    public_endpoint_port: PropertyRef = PropertyRef("public_endpoint_port")
    private_endpoint_dns: PropertyRef = PropertyRef("private_endpoint_dns")
    private_endpoint_port: PropertyRef = PropertyRef("private_endpoint_port")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayMongoDBInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayMongoDBInstance)
class ScalewayMongoDBInstanceToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayMongoDBInstanceToProjectRelProperties = (
        ScalewayMongoDBInstanceToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayMongoDBInstanceToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayMongoDBInstance)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
class ScalewayMongoDBInstanceToPrivateNetworkRel(CartographyRelSchema):
    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayMongoDBInstanceToPrivateNetworkRelProperties = (
        ScalewayMongoDBInstanceToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayMongoDBInstanceSchema(CartographyNodeSchema):
    label: str = "ScalewayMongoDBInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: ScalewayMongoDBInstanceProperties = ScalewayMongoDBInstanceProperties()
    sub_resource_relationship: ScalewayMongoDBInstanceToProjectRel = (
        ScalewayMongoDBInstanceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayMongoDBInstanceToPrivateNetworkRel(),
        ]
    )
