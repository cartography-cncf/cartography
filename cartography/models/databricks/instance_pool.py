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
from cartography.models.databricks.extra_labels import DATABRICKS_ACL_OBJECT


@dataclass(frozen=True)
class DatabricksInstancePoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the instance pool."
    )
    instance_pool_id: PropertyRef = PropertyRef(
        "instance_pool_id",
        extra_index=True,
        description="Databricks instance pool identifier.",
    )
    instance_pool_name: PropertyRef = PropertyRef(
        "instance_pool_name",
        extra_index=True,
        description="Name of the instance pool.",
    )
    node_type_id: PropertyRef = PropertyRef(
        "node_type_id", description="Node type provisioned by the instance pool."
    )
    min_idle_instances: PropertyRef = PropertyRef(
        "min_idle_instances",
        description="Minimum number of idle instances maintained by the pool.",
    )
    max_capacity: PropertyRef = PropertyRef(
        "max_capacity",
        description="Maximum number of instances the pool can contain.",
    )
    idle_instance_autotermination_minutes: PropertyRef = PropertyRef(
        "idle_instance_autotermination_minutes",
        description="Minutes before an idle instance terminates automatically.",
    )
    enable_elastic_disk: PropertyRef = PropertyRef(
        "enable_elastic_disk",
        description="Whether elastic disk autoscaling is enabled.",
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current lifecycle state of the instance pool."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksInstancePoolToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksInstancePool)
class DatabricksInstancePoolToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the instance pool as a resource."""

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
    """A Databricks pool of reusable compute instances."""

    label: str = "DatabricksInstancePool"
    properties: DatabricksInstancePoolNodeProperties = (
        DatabricksInstancePoolNodeProperties()
    )
    sub_resource_relationship: DatabricksInstancePoolToWorkspaceRel = (
        DatabricksInstancePoolToWorkspaceRel()
    )
    # ACL-target ontology label so the HAS_PERMISSION MatchLinks can target it.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABRICKS_ACL_OBJECT])
