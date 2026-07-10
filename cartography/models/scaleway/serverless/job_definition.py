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
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    image_uri: PropertyRef = PropertyRef("image_uri", extra_index=True)
    command: PropertyRef = PropertyRef("command")
    cpu_limit: PropertyRef = PropertyRef("cpu_limit")
    memory_limit: PropertyRef = PropertyRef("memory_limit")
    local_storage_capacity: PropertyRef = PropertyRef("local_storage_capacity")
    job_timeout: PropertyRef = PropertyRef("job_timeout")
    # Flattened from the nested cron_schedule object.
    cron_schedule: PropertyRef = PropertyRef("cron_schedule")
    cron_timezone: PropertyRef = PropertyRef("cron_timezone")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayServerlessJobDefinitionToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessJobDefinition)
class ScalewayServerlessJobDefinitionToProjectRel(CartographyRelSchema):
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
    label: str = "ScalewayServerlessJobDefinition"
    properties: ScalewayServerlessJobDefinitionProperties = (
        ScalewayServerlessJobDefinitionProperties()
    )
    sub_resource_relationship: ScalewayServerlessJobDefinitionToProjectRel = (
        ScalewayServerlessJobDefinitionToProjectRel()
    )
