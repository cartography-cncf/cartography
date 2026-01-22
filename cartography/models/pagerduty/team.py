from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class PagerDutyTeamProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    html_url: PropertyRef = PropertyRef("html_url")
    type: PropertyRef = PropertyRef("type")
    summary: PropertyRef = PropertyRef("summary")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    default_role: PropertyRef = PropertyRef("default_role")


@dataclass(frozen=True)
class PagerDutyTeamSchema(CartographyNodeSchema):
    label: str = "PagerDutyTeam"
    properties: PagerDutyTeamProperties = PagerDutyTeamProperties()
    # Cleanup is disabled because the MEMBER_OF relationship with role property
    # is loaded separately via Cypher query, not through the datamodel.
    # See https://github.com/cartography-cncf/cartography/issues/1589
    scoped_cleanup: bool = False
