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
class ScalewayServerlessJobDefinitionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Job definition UUID."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Job definition name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Job description."
    )
    image_uri: PropertyRef = PropertyRef(
        "image_uri",
        extra_index=True,
        description="Container image URI executed by the job.",
    )
    command: PropertyRef = PropertyRef(
        "command", description="Command run inside the container."
    )
    cpu_limit: PropertyRef = PropertyRef("cpu_limit", description="CPU limit in mvCPU.")
    memory_limit: PropertyRef = PropertyRef(
        "memory_limit", description="Memory limit in MB."
    )
    local_storage_capacity: PropertyRef = PropertyRef(
        "local_storage_capacity", description="Local storage capacity in MB."
    )
    job_timeout: PropertyRef = PropertyRef(
        "job_timeout", description="Per-run timeout (e.g. `3600s`)."
    )
    # Flattened from the nested cron_schedule object.
    cron_schedule: PropertyRef = PropertyRef(
        "cron_schedule", description="Cron expression, if the job is scheduled."
    )
    cron_timezone: PropertyRef = PropertyRef(
        "cron_timezone", description="Timezone for the cron schedule."
    )
    region: PropertyRef = PropertyRef("region", description="Region the job lives in.")
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
class ScalewayServerlessJobDefinitionToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessJobDefinition)
class ScalewayServerlessJobDefinitionToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayServerlessJobDefinition` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayServerlessJobDefinitionToProjectRelProperties = (
        ScalewayServerlessJobDefinitionToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessJobDefinitionSchema(CartographyNodeSchema):
    """Represents a Scaleway Serverless Job definition (a runnable, optionally scheduled,
    container job).
    """

    label: str = "ScalewayServerlessJobDefinition"
    properties: ScalewayServerlessJobDefinitionProperties = (
        ScalewayServerlessJobDefinitionProperties()
    )
    sub_resource_relationship: ScalewayServerlessJobDefinitionToProjectRel = (
        ScalewayServerlessJobDefinitionToProjectRel()
    )
