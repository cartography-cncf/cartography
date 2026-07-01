from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DatabricksInstancePoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    instance_pool_id: PropertyRef = PropertyRef("instance_pool_id", extra_index=True)
    instance_pool_name: PropertyRef = PropertyRef(
        "instance_pool_name", extra_index=True
    )
    node_type_id: PropertyRef = PropertyRef("node_type_id")
    min_idle_instances: PropertyRef = PropertyRef("min_idle_instances")
    max_capacity: PropertyRef = PropertyRef("max_capacity")
    idle_instance_autotermination_minutes: PropertyRef = PropertyRef(
        "idle_instance_autotermination_minutes"
    )
    enable_elastic_disk: PropertyRef = PropertyRef("enable_elastic_disk")
    state: PropertyRef = PropertyRef("state")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksInstancePoolToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksInstancePool)
class DatabricksInstancePoolToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksInstancePoolToWorkspaceRelProperties = (
        DatabricksInstancePoolToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksInstancePoolSchema(CartographyNodeSchema):
    label: str = "DatabricksInstancePool"
    properties: DatabricksInstancePoolNodeProperties = (
        DatabricksInstancePoolNodeProperties()
    )
    sub_resource_relationship: DatabricksInstancePoolToWorkspaceRel = (
        DatabricksInstancePoolToWorkspaceRel()
    )
