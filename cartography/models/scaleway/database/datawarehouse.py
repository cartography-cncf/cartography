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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    status: PropertyRef = PropertyRef("status")
    tags: PropertyRef = PropertyRef("tags")
    version: PropertyRef = PropertyRef("version")
    replica_count: PropertyRef = PropertyRef("replica_count")
    shard_count: PropertyRef = PropertyRef("shard_count")
    cpu_min: PropertyRef = PropertyRef("cpu_min")
    cpu_max: PropertyRef = PropertyRef("cpu_max")
    ram_per_cpu: PropertyRef = PropertyRef("ram_per_cpu")
    # Derived from the endpoints list: true if any endpoint is public-facing.
    is_public: PropertyRef = PropertyRef("is_public")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayDataWarehouseDeploymentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayDataWarehouseDeployment)
class ScalewayDataWarehouseDeploymentToProjectRel(CartographyRelSchema):
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
    label: str = "ScalewayDataWarehouseDeployment"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: ScalewayDataWarehouseDeploymentProperties = (
        ScalewayDataWarehouseDeploymentProperties()
    )
    sub_resource_relationship: ScalewayDataWarehouseDeploymentToProjectRel = (
        ScalewayDataWarehouseDeploymentToProjectRel()
    )
