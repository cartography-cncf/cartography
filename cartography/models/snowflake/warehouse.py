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
from cartography.models.ontology.labels import COMPUTE_CLUSTER
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeWarehouseNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the warehouse."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The warehouse name."
    )
    warehouse_type: PropertyRef = PropertyRef(
        "warehouse_type",
        description=(
            "Warehouse type: STANDARD, or a SNOWPARK-OPTIMIZED variant for "
            "memory-intensive workloads."
        ),
    )
    size: PropertyRef = PropertyRef(
        "size",
        description="Warehouse size (X-Small through 6X-Large), which sets its credit rate.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Whether the warehouse is STARTED, SUSPENDED or RESIZING.",
    )
    min_cluster_count: PropertyRef = PropertyRef(
        "min_cluster_count",
        description="Minimum number of clusters in a multi-cluster warehouse.",
    )
    max_cluster_count: PropertyRef = PropertyRef(
        "max_cluster_count",
        description="Maximum number of clusters a multi-cluster warehouse may scale out to.",
    )
    scaling_policy: PropertyRef = PropertyRef(
        "scaling_policy",
        description="Multi-cluster scaling policy: STANDARD or ECONOMY.",
    )
    auto_suspend: PropertyRef = PropertyRef(
        "auto_suspend",
        description=(
            "Seconds of inactivity before the warehouse suspends. Null means it never "
            "suspends and keeps billing credits."
        ),
    )
    auto_resume: PropertyRef = PropertyRef(
        "auto_resume",
        description="Whether a query against a suspended warehouse restarts it automatically.",
    )
    resource_monitor: PropertyRef = PropertyRef(
        "resource_monitor",
        description=(
            "Name of the resource monitor capping this warehouse's credit usage. Null "
            "when the warehouse has no credit ceiling of its own."
        ),
    )
    enable_query_acceleration: PropertyRef = PropertyRef(
        "enable_query_acceleration",
        description="Whether the query acceleration service is enabled for the warehouse.",
    )
    max_concurrency_level: PropertyRef = PropertyRef(
        "max_concurrency_level",
        description="Maximum number of concurrent statements a single cluster will run.",
    )
    statement_timeout_in_seconds: PropertyRef = PropertyRef(
        "statement_timeout_in_seconds",
        description="Seconds after which a statement running on the warehouse is aborted.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the warehouse."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owning role is an account ROLE or a DATABASE_ROLE.",
    )
    budget: PropertyRef = PropertyRef(
        "budget",
        description="Name of the budget the warehouse's spend is attributed to.",
    )
    kind: PropertyRef = PropertyRef(
        "kind", description="Warehouse kind reported by Snowflake."
    )
    comment: PropertyRef = PropertyRef("comment", description="Warehouse comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the warehouse was created."
    )
    resumed_on: PropertyRef = PropertyRef(
        "resumed_on", description="When the warehouse was last resumed."
    )
    updated_on: PropertyRef = PropertyRef(
        "updated_on", description="When the warehouse was last altered."
    )


@dataclass(frozen=True)
class SnowflakeWarehouseToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeWarehouse)
class SnowflakeWarehouseToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the warehouse as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeWarehouseToAccountRelProperties = (
        SnowflakeWarehouseToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeWarehouseToResourceMonitorRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeWarehouse)-[:MONITORED_BY]->(:SnowflakeResourceMonitor)
class SnowflakeWarehouseToResourceMonitorRel(CartographyRelSchema):
    """A resource monitor caps the credits this Snowflake warehouse may consume."""

    target_node_label: str = "SnowflakeResourceMonitor"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_monitor_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORED_BY"
    properties: SnowflakeWarehouseToResourceMonitorRelProperties = (
        SnowflakeWarehouseToResourceMonitorRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeWarehouseSchema(CartographyNodeSchema):
    """Represents a Snowflake virtual warehouse: the compute cluster that executes queries."""

    label: str = "SnowflakeWarehouse"
    properties: SnowflakeWarehouseNodeProperties = SnowflakeWarehouseNodeProperties()
    # ComputeCluster: ontology label; a warehouse is an elastic compute cluster.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [COMPUTE_CLUSTER, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeWarehouseToAccountRel = (
        SnowflakeWarehouseToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeWarehouseToResourceMonitorRel()],
    )
