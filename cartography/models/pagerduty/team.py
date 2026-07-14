from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class PagerDutyTeamProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Team ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    html_url: PropertyRef = PropertyRef(
        "html_url", description="PagerDuty web URL for the team."
    )
    type: PropertyRef = PropertyRef(
        "type", description="PagerDuty object type for the team."
    )
    summary: PropertyRef = PropertyRef(
        "summary", description="Short summary of the team."
    )
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Team name.")
    description: PropertyRef = PropertyRef(
        "description", description="Team description."
    )
    default_role: PropertyRef = PropertyRef(
        "default_role", description="Default role assigned to team members."
    )


@dataclass(frozen=True)
class PagerDutyTeamSchema(CartographyNodeSchema):
    """A PagerDuty team with the canonical UserGroup label."""

    label: str = "PagerDutyTeam"
    properties: PagerDutyTeamProperties = PagerDutyTeamProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
    # Cleanup is disabled because the MEMBER_OF relationship with role property
    # is loaded separately via Cypher query, not through the datamodel.
    # See https://github.com/cartography-cncf/cartography/issues/1589
    scoped_cleanup: bool = False
