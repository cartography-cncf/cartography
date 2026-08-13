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
from cartography.models.ontology.labels import COMPUTE_CLUSTER
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeComputePoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the compute pool."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The compute pool name."
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Whether the pool is ACTIVE, IDLE, SUSPENDED, STARTING or STOPPING.",
    )
    min_nodes: PropertyRef = PropertyRef(
        "min_nodes", description="Minimum number of nodes the pool keeps running."
    )
    max_nodes: PropertyRef = PropertyRef(
        "max_nodes", description="Maximum number of nodes the pool may scale out to."
    )
    active_nodes: PropertyRef = PropertyRef(
        "active_nodes", description="Number of nodes currently running in the pool."
    )
    instance_family: PropertyRef = PropertyRef(
        "instance_family",
        description="Snowflake instance family that determines each node's CPU, memory and GPUs.",
    )
    num_services: PropertyRef = PropertyRef(
        "num_services", description="Number of long-running services on the pool."
    )
    num_jobs: PropertyRef = PropertyRef(
        "num_jobs", description="Number of job services currently on the pool."
    )
    is_exclusive: PropertyRef = PropertyRef(
        "is_exclusive",
        description=(
            "Whether the pool is dedicated to a single Snowflake Native App rather than "
            "shared across the account's own services."
        ),
    )
    application: PropertyRef = PropertyRef(
        "application",
        description="Name of the Native App the pool is exclusive to, when it is exclusive.",
    )
    auto_resume: PropertyRef = PropertyRef(
        "auto_resume",
        description="Whether the pool restarts automatically when a service needs it.",
    )
    auto_suspend_secs: PropertyRef = PropertyRef(
        "auto_suspend_secs",
        description="Seconds of inactivity before the pool suspends its nodes.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the compute pool."
    )
    comment: PropertyRef = PropertyRef("comment", description="Compute pool comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the compute pool was created."
    )


@dataclass(frozen=True)
class SnowflakeComputePoolToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeComputePool)
class SnowflakeComputePoolToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the compute pool as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeComputePoolToAccountRelProperties = (
        SnowflakeComputePoolToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeComputePoolSchema(CartographyNodeSchema):
    """Represents a Snowflake compute pool: the node pool that runs Snowpark Container Services workloads."""

    label: str = "SnowflakeComputePool"
    properties: SnowflakeComputePoolNodeProperties = (
        SnowflakeComputePoolNodeProperties()
    )
    # ComputeCluster: ontology label; a compute pool is a cluster of container hosts.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [COMPUTE_CLUSTER, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeComputePoolToAccountRel = (
        SnowflakeComputePoolToAccountRel()
    )
