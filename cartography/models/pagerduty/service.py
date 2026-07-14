from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class PagerDutyServiceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Service ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    html_url: PropertyRef = PropertyRef(
        "html_url", description="PagerDuty web URL for the service."
    )
    type: PropertyRef = PropertyRef(
        "type", description="PagerDuty object type for the service."
    )
    summary: PropertyRef = PropertyRef(
        "summary", description="Short summary of the service."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Service name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Service description."
    )
    auto_resolve_timeout: PropertyRef = PropertyRef(
        "auto_resolve_timeout",
        description="Seconds before an open incident resolves automatically.",
    )
    acknowledgement_timeout: PropertyRef = PropertyRef(
        "acknowledgement_timeout",
        description="Seconds before an acknowledged incident becomes triggered.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the service was created."
    )
    status: PropertyRef = PropertyRef("status", description="Current service status.")
    alert_creation: PropertyRef = PropertyRef(
        "alert_creation", description="Whether the service creates alerts."
    )
    alert_grouping_parameters_type: PropertyRef = PropertyRef(
        "alert_grouping_parameters_type",
        description="Alert grouping strategy used by the service.",
    )
    incident_urgency_rule_type: PropertyRef = PropertyRef(
        "incident_urgency_rule_type",
        description="Type of incident urgency rule.",
    )
    incident_urgency_rule_during_support_hours_type: PropertyRef = PropertyRef(
        "incident_urgency_rule_during_support_hours_type",
        description="Urgency rule type used during support hours.",
    )
    incident_urgency_rule_during_support_hours_urgency: PropertyRef = PropertyRef(
        "incident_urgency_rule_during_support_hours_urgency",
        description="Incident urgency used during support hours.",
    )
    incident_urgency_rule_outside_support_hours_type: PropertyRef = PropertyRef(
        "incident_urgency_rule_outside_support_hours_type",
        description="Urgency rule type used outside support hours.",
    )
    incident_urgency_rule_outside_support_hours_urgency: PropertyRef = PropertyRef(
        "incident_urgency_rule_outside_support_hours_urgency",
        description="Incident urgency used outside support hours.",
    )
    support_hours_type: PropertyRef = PropertyRef(
        "support_hours_type", description="Type of configured support hours."
    )
    support_hours_time_zone: PropertyRef = PropertyRef(
        "support_hours_time_zone", description="Time zone used for support hours."
    )
    support_hours_start_time: PropertyRef = PropertyRef(
        "support_hours_start_time", description="Daily start time for support hours."
    )
    support_hours_end_time: PropertyRef = PropertyRef(
        "support_hours_end_time", description="Daily end time for support hours."
    )
    support_hours_days_of_week: PropertyRef = PropertyRef(
        "support_hours_days_of_week",
        description="Days of the week included in support hours.",
    )


@dataclass(frozen=True)
class PagerDutyServiceToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyTeam)-[:ASSOCIATED_WITH]->(:PagerDutyService)
class PagerDutyServiceToTeamRel(CartographyRelSchema):
    """A team associated with a service."""

    target_node_label: str = "PagerDutyTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("teams_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: PagerDutyServiceToTeamRelProperties = (
        PagerDutyServiceToTeamRelProperties()
    )


@dataclass(frozen=True)
class PagerDutyServiceSchema(CartographyNodeSchema):
    """A PagerDuty service that receives and manages incidents."""

    label: str = "PagerDutyService"
    properties: PagerDutyServiceProperties = PagerDutyServiceProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PagerDutyServiceToTeamRel(),
        ]
    )
