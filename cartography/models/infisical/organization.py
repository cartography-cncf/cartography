from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class InfisicalOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable Infisical organization identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Infisical organization was last seen.",
    )
    api_url: PropertyRef = PropertyRef(
        "api_url",
        description="Infisical API origin used to ingest this organization.",
    )


@dataclass(frozen=True)
class InfisicalOrganizationSchema(CartographyNodeSchema):
    """An Infisical organization whose project metadata is ingested."""

    label: str = "InfisicalOrganization"
    properties: InfisicalOrganizationNodeProperties = (
        InfisicalOrganizationNodeProperties()
    )
    sub_resource_relationship: None = None
    scoped_cleanup: bool = False
