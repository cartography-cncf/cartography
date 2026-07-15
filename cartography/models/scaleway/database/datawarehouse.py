from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayDataWarehouseDeploymentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the deployment.")
    name: PropertyRef = PropertyRef("name", description="Name of the deployment.")
    status: PropertyRef = PropertyRef("status", description="Status of the deployment.")
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags attached to the deployment."
    )
    version: PropertyRef = PropertyRef("version", description="Engine version.")
    replica_count: PropertyRef = PropertyRef(
        "replica_count", description="Number of replicas."
    )
    shard_count: PropertyRef = PropertyRef(
        "shard_count", description="Number of shards."
    )
    cpu_min: PropertyRef = PropertyRef("cpu_min", description="Minimum vCPU.")
    cpu_max: PropertyRef = PropertyRef("cpu_max", description="Maximum vCPU.")
    ram_per_cpu: PropertyRef = PropertyRef("ram_per_cpu", description="RAM per vCPU.")
    # Derived from the endpoints list: true if any endpoint is public-facing.
    is_public: PropertyRef = PropertyRef(
        "is_public", description="True if any endpoint is public-facing."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the deployment lives in."
    )
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
class ScalewayDataWarehouseDeploymentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayDataWarehouseDeployment)
class ScalewayDataWarehouseDeploymentToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayDataWarehouseDeployment` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayDataWarehouseDeploymentToProjectRelProperties = (
        ScalewayDataWarehouseDeploymentToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayDataWarehouseDeploymentSchema(CartographyNodeSchema):
    """Represents a Data Warehouse (ClickHouse) deployment in Scaleway."""

    label: str = "ScalewayDataWarehouseDeployment"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: ScalewayDataWarehouseDeploymentProperties = (
        ScalewayDataWarehouseDeploymentProperties()
    )
    sub_resource_relationship: ScalewayDataWarehouseDeploymentToProjectRel = (
        ScalewayDataWarehouseDeploymentToProjectRel()
    )
