from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class JFrogArtifactoryTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    base_url: PropertyRef = PropertyRef("base_url")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JFrogArtifactoryTenantSchema(CartographyNodeSchema):
    label: str = "JFrogArtifactoryTenant"
    properties: JFrogArtifactoryTenantNodeProperties = (
        JFrogArtifactoryTenantNodeProperties()
    )
