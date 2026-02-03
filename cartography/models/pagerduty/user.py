from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties


@dataclass(frozen=True)
class PagerDutyUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    html_url: PropertyRef = PropertyRef("html_url")
    type: PropertyRef = PropertyRef("type")
    summary: PropertyRef = PropertyRef("summary")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    time_zone: PropertyRef = PropertyRef("time_zone")
    color: PropertyRef = PropertyRef("color")
    role: PropertyRef = PropertyRef("role")
    avatar_url: PropertyRef = PropertyRef("avatar_url")
    description: PropertyRef = PropertyRef("description")
    invitation_sent: PropertyRef = PropertyRef("invitation_sent")
    job_title: PropertyRef = PropertyRef("job_title")


@dataclass(frozen=True)
class PagerDutyUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PagerDutyUserSchema(CartographyNodeSchema):
    label: str = "PagerDutyUser"
    properties: PagerDutyUserProperties = PagerDutyUserProperties()
    scoped_cleanup: bool = False
