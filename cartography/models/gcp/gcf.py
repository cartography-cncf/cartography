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
class GCPCloudFunctionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="The full, unique resource name of the function.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="The full, unique resource name of the function (same as id).",
    )
    description: PropertyRef = PropertyRef(
        "description", description="User-provided description of the function."
    )
    runtime: PropertyRef = PropertyRef(
        "runtime",
        description="The language runtime environment for the function (e.g., python310).",
    )
    available_memory_mb: PropertyRef = PropertyRef(
        "available_memory_mb",
        description="Memory allocated to the function, in MB (from `availableMemoryMb`).",
    )
    timeout: PropertyRef = PropertyRef(
        "timeout",
        description="Maximum execution time, in seconds (parsed from the API's Duration string; whole-second values are stored as int, fractional values as float).",
    )
    entry_point: PropertyRef = PropertyRef(
        "entryPoint",
        description="The name of the function within the source code to be executed.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="The current state of the function (e.g., ACTIVE, OFFLINE, DEPLOY_IN_PROGRESS).",
    )
    update_time: PropertyRef = PropertyRef(
        "updateTime", description="The timestamp when the function was last modified."
    )
    service_account_email: PropertyRef = PropertyRef(
        "serviceAccountEmail",
        description="The email of the service account the function runs as.",
    )
    https_trigger_url: PropertyRef = PropertyRef(
        "https_trigger_url",
        description="The public URL if the function is triggered by an HTTP request.",
    )
    event_trigger_type: PropertyRef = PropertyRef(
        "event_trigger_type",
        description="The type of event that triggers the function (e.g., a Pub/Sub message).",
    )
    event_trigger_resource: PropertyRef = PropertyRef(
        "event_trigger_resource",
        description="The specific resource the event trigger monitors.",
    )
    project_id: PropertyRef = PropertyRef(
        "projectId",
        set_in_kwargs=True,
        description="The ID of the GCP project to which the function belongs.",
    )
    region: PropertyRef = PropertyRef(
        "region",
        set_in_kwargs=True,
        description="The GCP region where the function is deployed.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of when the data was last updated in the graph.",
    )


@dataclass(frozen=True)
class GCPCloudFunctionToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPCloudFunctionToGCPProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPCloudFunctionToGCPProjectRelProperties = (
        GCPCloudFunctionToGCPProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudFunctionToGCPServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPCloudFunctionToGCPServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("serviceAccountEmail")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: GCPCloudFunctionToGCPServiceAccountRelProperties = (
        GCPCloudFunctionToGCPServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudFunctionSchema(CartographyNodeSchema):
    """Representation of a Google [Cloud Function](https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions) (v1 API)."""

    label: str = "GCPCloudFunction"
    properties: GCPCloudFunctionProperties = GCPCloudFunctionProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Function"])
    sub_resource_relationship: GCPCloudFunctionToGCPProjectRel = (
        GCPCloudFunctionToGCPProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPCloudFunctionToGCPServiceAccountRel(),
        ],
    )
