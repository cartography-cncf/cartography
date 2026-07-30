from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class GCPProjectComputeMetadataNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    compute_project_enable_oslogin: PropertyRef = PropertyRef(
        "compute_project_enable_oslogin",
    )


@dataclass(frozen=True)
class GCPProjectComputeMetadataSchema(CartographyNodeSchema):
    """Composite schema for Compute API properties on an existing GCP project."""

    label: str = "GCPProject"
    properties: GCPProjectComputeMetadataNodeProperties = (
        GCPProjectComputeMetadataNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    scoped_cleanup: bool = False
