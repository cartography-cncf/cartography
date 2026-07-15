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
class ScalewayRdbInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    engine: PropertyRef = PropertyRef("engine")
    node_type: PropertyRef = PropertyRef("node_type")
    is_ha_cluster: PropertyRef = PropertyRef("is_ha_cluster")
    encryption_at_rest_enabled: PropertyRef = PropertyRef("encryption_at_rest_enabled")
    volume_type: PropertyRef = PropertyRef("volume_type")
    volume_size: PropertyRef = PropertyRef("volume_size")
    backup_schedule_disabled: PropertyRef = PropertyRef("backup_schedule_disabled")
    backup_schedule_retention_days: PropertyRef = PropertyRef(
        "backup_schedule_retention_days"
    )
    backup_same_region: PropertyRef = PropertyRef("backup_same_region")
    tags: PropertyRef = PropertyRef("tags")
    # Endpoint summary fields (flattened from the endpoints list).
    is_public: PropertyRef = PropertyRef("is_public")
    public_endpoint_ip: PropertyRef = PropertyRef("public_endpoint_ip")
    public_endpoint_hostname: PropertyRef = PropertyRef("public_endpoint_hostname")
    public_endpoint_port: PropertyRef = PropertyRef("public_endpoint_port")
    private_endpoint_ip: PropertyRef = PropertyRef("private_endpoint_ip")
    private_endpoint_port: PropertyRef = PropertyRef("private_endpoint_port")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayRdbInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayRdbInstance)
class ScalewayRdbInstanceToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayRdbInstanceToProjectRelProperties = (
        ScalewayRdbInstanceToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayRdbInstanceToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayRdbInstance)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
class ScalewayRdbInstanceToPrivateNetworkRel(CartographyRelSchema):
    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayRdbInstanceToPrivateNetworkRelProperties = (
        ScalewayRdbInstanceToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayRdbInstanceSchema(CartographyNodeSchema):
    label: str = "ScalewayRdbInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: ScalewayRdbInstanceProperties = ScalewayRdbInstanceProperties()
    sub_resource_relationship: ScalewayRdbInstanceToProjectRel = (
        ScalewayRdbInstanceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayRdbInstanceToPrivateNetworkRel(),
        ]
    )
