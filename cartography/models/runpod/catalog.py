from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.runpod._relationships import RunPodToAccountRel


@dataclass(frozen=True)
class RunPodDataCenterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the RunPod data center.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "account_id", description="Configured RunPod account identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the data center."
    )
    location: PropertyRef = PropertyRef("location", description="Data center location.")
    country_code: PropertyRef = PropertyRef("country_code", description="Country code.")
    gpu_type_ids: PropertyRef = PropertyRef(
        "gpu_type_ids", description="GPU type IDs available in this data center."
    )
    compliance: PropertyRef = PropertyRef(
        "compliance", description="Compliance programs advertised for this data center."
    )
    volume_types: PropertyRef = PropertyRef(
        "volume_types", description="Supported network volume types."
    )
    global_networking: PropertyRef = PropertyRef(
        "global_networking", description="Whether global networking is supported."
    )


@dataclass(frozen=True)
class RunPodDataCenterSchema(CartographyNodeSchema):
    """A RunPod catalog data center visible to the configured account."""

    label: str = "RunPodDataCenter"
    properties: RunPodDataCenterNodeProperties = RunPodDataCenterNodeProperties()
    sub_resource_relationship: RunPodToAccountRel = RunPodToAccountRel()
