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
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Instance UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Instance name."
    )
    status: PropertyRef = PropertyRef("status", description="Instance status.")
    version: PropertyRef = PropertyRef(
        "version", description="MongoDB version (e.g. `7.0`)."
    )
    node_type: PropertyRef = PropertyRef(
        "node_type", description="Commercial node type."
    )
    node_amount: PropertyRef = PropertyRef(
        "node_amount", description="Number of nodes in the deployment."
    )
    volume_type: PropertyRef = PropertyRef(
        "volume_type", description="Storage volume type."
    )
    volume_size: PropertyRef = PropertyRef(
        "volume_size", description="Storage volume size in bytes."
    )
    tags: PropertyRef = PropertyRef("tags", description="Instance tags.")
    # Endpoint summary fields (flattened from the endpoints list).
    is_public: PropertyRef = PropertyRef(
        "is_public",
        description="True if the instance exposes a publicly reachable endpoint.",
    )
    public_endpoint_dns: PropertyRef = PropertyRef(
        "public_endpoint_dns", description="DNS record for the public endpoint, if any."
    )
    public_endpoint_port: PropertyRef = PropertyRef(
        "public_endpoint_port", description="Port of the public endpoint, if any."
    )
    private_endpoint_dns: PropertyRef = PropertyRef(
        "private_endpoint_dns",
        description="DNS record for the first private-network endpoint, if any.",
    )
    private_endpoint_port: PropertyRef = PropertyRef(
        "private_endpoint_port",
        description="Port of the first private-network endpoint, if any.",
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the instance lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )


@dataclass(frozen=True)
class ScalewayMongoDBInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayMongoDBInstance)
class ScalewayMongoDBInstanceToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayMongoDBInstance` through `RESOURCE`."""

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
    """Connects `ScalewayMongoDBInstance` to `ScalewayPrivateNetwork` through
    `ATTACHED_TO`.
    """

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
    """Represents a managed MongoDB instance (Scaleway "Managed Database for MongoDB")."""

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
