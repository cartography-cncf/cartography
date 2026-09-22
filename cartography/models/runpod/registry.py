from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import SECRET
from cartography.models.runpod._relationships import RunPodToAccountRel


@dataclass(frozen=True)
class RunPodRegistryCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="ID of the RunPod registry credential."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    account_id: PropertyRef = PropertyRef(
        "account_id", description="Configured RunPod account identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Display name of the registry credential."
    )


@dataclass(frozen=True)
class RunPodRegistryCredentialSchema(CartographyNodeSchema):
    """
    A RunPod container registry credential.

    Only metadata is ingested. The credential secret value is not stored.
    """

    label: str = "RunPodRegistryCredential"
    properties: RunPodRegistryCredentialNodeProperties = (
        RunPodRegistryCredentialNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    sub_resource_relationship: RunPodToAccountRel = RunPodToAccountRel()
