from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class TerraformWorkspaceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("lineage")
    lineage: PropertyRef = PropertyRef("lineage")
    terraform_version: PropertyRef = PropertyRef("terraform_version")
    serial: PropertyRef = PropertyRef("serial")
    workspace_name: PropertyRef = PropertyRef("workspace_name")
    source_uri: PropertyRef = PropertyRef("source_uri", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TerraformWorkspaceSchema(CartographyNodeSchema):
    label: str = "TerraformWorkspace"
    properties: TerraformWorkspaceProperties = TerraformWorkspaceProperties()
