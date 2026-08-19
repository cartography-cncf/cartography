from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.runpod._relationships import RunPodResourceRelProperties
from cartography.models.runpod._relationships import RunPodToAccountRel


@dataclass(frozen=True)
class RunPodClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the RunPod cluster.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "account_id", description="Configured RunPod account identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the cluster."
    )
    status: PropertyRef = PropertyRef("status", description="Current cluster status.")
    data_center_id: PropertyRef = PropertyRef(
        "data_center_id", extra_index=True, description="RunPod data center ID."
    )
    gpu_type_id: PropertyRef = PropertyRef("gpu_type_id", description="GPU type ID.")
    gpu_count: PropertyRef = PropertyRef("gpu_count", description="Total GPU count.")
    pod_count: PropertyRef = PropertyRef("pod_count", description="Cluster pod count.")
    running_pod_count: PropertyRef = PropertyRef(
        "running_pod_count", description="Running pod count."
    )
    primary_pod_id: PropertyRef = PropertyRef(
        "primary_pod_id", extra_index=True, description="Primary pod ID."
    )
    template_id: PropertyRef = PropertyRef(
        "template_id", extra_index=True, description="Template used by the cluster."
    )
    created_at: PropertyRef = PropertyRef("created_at", description="Creation time.")


@dataclass(frozen=True)
class RunPodClusterToPrimaryPodRel(CartographyRelSchema):
    """Connects a cluster to its primary pod."""

    target_node_label: str = "RunPodPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("primary_pod_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PRIMARY"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodClusterToTemplateRel(CartographyRelSchema):
    """Connects a cluster to the template used by its pods."""

    target_node_label: str = "RunPodTemplate"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("template_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_TEMPLATE"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodClusterToDataCenterRel(CartographyRelSchema):
    """Connects a cluster to the data center where it runs."""

    target_node_label: str = "RunPodDataCenter"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("data_center_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_IN"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodClusterSchema(CartographyNodeSchema):
    """A RunPod cluster grouping multiple pods."""

    label: str = "RunPodCluster"
    properties: RunPodClusterNodeProperties = RunPodClusterNodeProperties()
    sub_resource_relationship: RunPodToAccountRel = RunPodToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RunPodClusterToPrimaryPodRel(),
            RunPodClusterToTemplateRel(),
            RunPodClusterToDataCenterRel(),
        ],
    )
