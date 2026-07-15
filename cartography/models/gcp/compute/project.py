from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class GCPProjectComputeMetadataNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )
    compute_project_enable_oslogin: PropertyRef = PropertyRef(
        "compute_project_enable_oslogin",
        description="Project metadata setting that enables OS Login for Compute Engine instances.",
    )


@dataclass(frozen=True)
class GCPProjectComputeMetadataSchema(CartographyNodeSchema):
    """A Google Cloud Project resource."""

    label: str = "GCPProject"
    properties: GCPProjectComputeMetadataNodeProperties = (
        GCPProjectComputeMetadataNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    scoped_cleanup: bool = False
