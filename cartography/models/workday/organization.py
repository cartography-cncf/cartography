from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class WorkdayOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Supervisory_Organization")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("Supervisory_Organization")


@dataclass(frozen=True)
class WorkdayOrganizationSchema(CartographyNodeSchema):
    label: str = "WorkdayOrganization"
    properties: WorkdayOrganizationNodeProperties = WorkdayOrganizationNodeProperties()

    @property
    def scoped_cleanup(self) -> bool:
        return False
