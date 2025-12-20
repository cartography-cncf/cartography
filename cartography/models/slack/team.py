from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class SlackTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    domain: PropertyRef = PropertyRef("domain")
    url: PropertyRef = PropertyRef("url")
    is_verified: PropertyRef = PropertyRef("is_verified")
    email_domain: PropertyRef = PropertyRef("email_domain")


@dataclass(frozen=True)
class SlackTeamSchema(CartographyNodeSchema):
    label: str = "SlackTeam"
    properties: SlackTeamNodeProperties = SlackTeamNodeProperties()
