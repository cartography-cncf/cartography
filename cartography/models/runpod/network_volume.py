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
class RunPodNetworkVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the RunPod network volume.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "account_id", description="Configured RunPod account identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the network volume."
    )
    size: PropertyRef = PropertyRef("size", description="Volume size in GiB.")
    volume_type: PropertyRef = PropertyRef("volume_type", description="Volume type.")
    data_center_id: PropertyRef = PropertyRef(
        "data_center_id", extra_index=True, description="RunPod data center ID."
    )
    created_at: PropertyRef = PropertyRef("created_at", description="Creation time.")


@dataclass(frozen=True)
class RunPodNetworkVolumeToDataCenterRel(CartographyRelSchema):
    """Connects a network volume to the data center where it is available."""

    target_node_label: str = "RunPodDataCenter"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("data_center_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LOCATED_IN"
    properties: RunPodResourceRelProperties = RunPodResourceRelProperties()


@dataclass(frozen=True)
class RunPodNetworkVolumeSchema(CartographyNodeSchema):
    """A RunPod persistent network volume."""

    label: str = "RunPodNetworkVolume"
    properties: RunPodNetworkVolumeNodeProperties = RunPodNetworkVolumeNodeProperties()
    sub_resource_relationship: RunPodToAccountRel = RunPodToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RunPodNetworkVolumeToDataCenterRel()],
    )
