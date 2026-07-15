from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class PagerDutyUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="User ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    html_url: PropertyRef = PropertyRef(
        "html_url", description="PagerDuty web URL for the user."
    )
    type: PropertyRef = PropertyRef(
        "type", description="PagerDuty object type for the user."
    )
    summary: PropertyRef = PropertyRef(
        "summary", description="Short summary of the user."
    )
    name: PropertyRef = PropertyRef("name", extra_index=True, description="User name.")
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    time_zone: PropertyRef = PropertyRef(
        "time_zone", description="Preferred time zone for the user."
    )
    color: PropertyRef = PropertyRef(
        "color", description="Color used for the user in schedules."
    )
    role: PropertyRef = PropertyRef("role", description="User account role.")
    avatar_url: PropertyRef = PropertyRef(
        "avatar_url", description="URL of the user's avatar."
    )
    description: PropertyRef = PropertyRef("description", description="User biography.")
    invitation_sent: PropertyRef = PropertyRef(
        "invitation_sent", description="Whether the user has a pending invitation."
    )
    job_title: PropertyRef = PropertyRef("job_title", description="User job title.")


@dataclass(frozen=True)
class PagerDutyUserSchema(CartographyNodeSchema):
    """A PagerDuty user account with the canonical UserAccount label."""

    label: str = "PagerDutyUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: PagerDutyUserProperties = PagerDutyUserProperties()
    scoped_cleanup: bool = False
