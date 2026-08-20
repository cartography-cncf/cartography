from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import COMPUTE_SERVICE
from cartography.models.runpod._relationships import RunPodResourceRelProperties
from cartography.models.runpod._relationships import RunPodToAccountRel


@dataclass(frozen=True)
class RunPodServerlessEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="ID of the RunPod serverless endpoint."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "account_id", description="Configured RunPod account identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the endpoint."
    )
    endpoint_type: PropertyRef = PropertyRef(
        "endpoint_type", description="Endpoint type."
    )
    image_name: PropertyRef = PropertyRef("image_name", description="Container image.")
    gpu_type_ids: PropertyRef = PropertyRef("gpu_type_ids", description="GPU type IDs.")
    data_center_ids: PropertyRef = PropertyRef(
        "data_center_ids", description="Allowed data center IDs."
    )
    network_volume_ids: PropertyRef = PropertyRef(
        "network_volume_ids", description="Attached network volume IDs."
    )
    workers_min: PropertyRef = PropertyRef(
        "workers_min", description="Minimum worker count."
    )
    workers_max: PropertyRef = PropertyRef(
        "workers_max", description="Maximum worker count."
    )
    idle_timeout: PropertyRef = PropertyRef(
        "idle_timeout", description="Worker idle timeout in seconds."
    )
    scaler_type: PropertyRef = PropertyRef("scaler_type", description="Scaler type.")
    scaler_value: PropertyRef = PropertyRef("scaler_value", description="Scaler value.")
    timeout: PropertyRef = PropertyRef("timeout", description="Request timeout.")
    created_at: PropertyRef = PropertyRef("created_at", description="Creation time.")
    ports: PropertyRef = PropertyRef("ports", description="Configured port summaries.")


@dataclass(frozen=True)
class RunPodServerlessEndpointToNetworkVolumeRel(CartographyRelSchema):
    """Connects a serverless endpoint to attached network volumes."""

    target_node_label: str = "RunPodNetworkVolume"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_volume_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_VOLUME"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodServerlessEndpointToDataCenterRel(CartographyRelSchema):
    """Connects a serverless endpoint to its allowed data centers."""

    target_node_label: str = "RunPodDataCenter"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("data_center_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_IN"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodServerlessEndpointSchema(CartographyNodeSchema):
    """A RunPod serverless endpoint and its scaling/runtime configuration."""

    label: str = "RunPodServerlessEndpoint"
    properties: RunPodServerlessEndpointNodeProperties = (
        RunPodServerlessEndpointNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
    sub_resource_relationship: RunPodToAccountRel = RunPodToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RunPodServerlessEndpointToNetworkVolumeRel(),
            RunPodServerlessEndpointToDataCenterRel(),
        ],
    )
