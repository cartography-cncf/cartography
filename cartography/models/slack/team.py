from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SlackTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Slack workspace ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Slack workspace name."
    )
    domain: PropertyRef = PropertyRef("domain", description="Slack workspace domain.")
    url: PropertyRef = PropertyRef("url", description="Slack workspace URL.")
    is_verified: PropertyRef = PropertyRef(
        "is_verified", description="Whether the workspace is verified."
    )
    email_domain: PropertyRef = PropertyRef(
        "email_domain", description="Email domain associated with the workspace."
    )


@dataclass(frozen=True)
class SlackTeamSchema(CartographyNodeSchema):
    """A Slack workspace with the canonical Tenant label."""

    label: str = "SlackTeam"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    properties: SlackTeamNodeProperties = SlackTeamNodeProperties()
