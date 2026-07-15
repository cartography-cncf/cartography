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
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Instance UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Instance name."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Instance status (`ready`, `provisioning`, ...)."
    )
    engine: PropertyRef = PropertyRef(
        "engine", description="Engine and version (e.g. `PostgreSQL-15`, `MySQL-8`)."
    )
    node_type: PropertyRef = PropertyRef(
        "node_type", description="Commercial node type (e.g. `DB-DEV-S`)."
    )
    is_ha_cluster: PropertyRef = PropertyRef(
        "is_ha_cluster",
        description="True if the instance runs in high-availability mode.",
    )
    encryption_at_rest_enabled: PropertyRef = PropertyRef(
        "encryption_at_rest_enabled",
        description="True if encryption at rest is enabled.",
    )
    volume_type: PropertyRef = PropertyRef(
        "volume_type",
        description="Storage volume type (`lssd`, `bssd`, `sbs_5k`, ...).",
    )
    volume_size: PropertyRef = PropertyRef(
        "volume_size", description="Storage volume size in bytes."
    )
    backup_schedule_disabled: PropertyRef = PropertyRef(
        "backup_schedule_disabled",
        description="True if automated backups are disabled.",
    )
    backup_schedule_retention_days: PropertyRef = PropertyRef(
        "backup_schedule_retention_days",
        description="Backup retention in days, when configured.",
    )
    backup_same_region: PropertyRef = PropertyRef(
        "backup_same_region",
        description="True if backups are stored in the same region as the instance.",
    )
    tags: PropertyRef = PropertyRef("tags", description="Instance tags.")
    # Endpoint summary fields (flattened from the endpoints list).
    is_public: PropertyRef = PropertyRef(
        "is_public",
        description="True if the instance exposes a publicly reachable endpoint (load balancer or direct access).",
    )
    public_endpoint_ip: PropertyRef = PropertyRef(
        "public_endpoint_ip", description="IP of the public endpoint, if any."
    )
    public_endpoint_hostname: PropertyRef = PropertyRef(
        "public_endpoint_hostname",
        description="Hostname of the public endpoint, if any.",
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
class ScalewayRdbInstanceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayRdbInstance)
class ScalewayRdbInstanceToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayRdbInstance` through `RESOURCE`."""

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
    """Connects `ScalewayRdbInstance` to `ScalewayPrivateNetwork` through `ATTACHED_TO`."""

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
    """Represents a managed PostgreSQL / MySQL database instance (Scaleway "Managed
    Database for PostgreSQL and MySQL").
    """

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
