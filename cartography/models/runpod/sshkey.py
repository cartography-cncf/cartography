from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.runpod._relationships import RunPodToAccountRel


@dataclass(frozen=True)
class RunPodSSHKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Stable SSH key fingerprint or ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "account_id", description="Configured RunPod account identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name for the SSH key."
    )
    fingerprint: PropertyRef = PropertyRef(
        "fingerprint", extra_index=True, description="SSH public key fingerprint."
    )
    created_at: PropertyRef = PropertyRef("created_at", description="Creation time.")


@dataclass(frozen=True)
class RunPodSSHKeySchema(CartographyNodeSchema):
    """An SSH public key registered on a RunPod account."""

    label: str = "RunPodSSHKey"
    properties: RunPodSSHKeyNodeProperties = RunPodSSHKeyNodeProperties()
    sub_resource_relationship: RunPodToAccountRel = RunPodToAccountRel()
