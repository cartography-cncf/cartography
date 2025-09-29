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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    html_url: PropertyRef = PropertyRef("html_url")
    type: PropertyRef = PropertyRef("type")
    summary: PropertyRef = PropertyRef("summary")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    auto_resolve_timeout: PropertyRef = PropertyRef("auto_resolve_timeout")
    acknowledgement_timeout: PropertyRef = PropertyRef("acknowledgement_timeout")
    created_at: PropertyRef = PropertyRef("created_at")
    status: PropertyRef = PropertyRef("status")
    alert_creation: PropertyRef = PropertyRef("alert_creation")
    alert_grouping_parameters_type: PropertyRef = PropertyRef(
        "alert_grouping_parameters_type"
    )
    incident_urgency_rule_type: PropertyRef = PropertyRef("incident_urgency_rule_type")
    incident_urgency_rule_during_support_hours_type: PropertyRef = PropertyRef(
        "incident_urgency_rule_during_support_hours_type"
    )
    incident_urgency_rule_during_support_hours_urgency: PropertyRef = PropertyRef(
        "incident_urgency_rule_during_support_hours_urgency"
    )
    incident_urgency_rule_outside_support_hours_type: PropertyRef = PropertyRef(
        "incident_urgency_rule_outside_support_hours_type"
    )
    incident_urgency_rule_outside_support_hours_urgency: PropertyRef = PropertyRef(
        "incident_urgency_rule_outside_support_hours_urgency"
    )
    support_hours_type: PropertyRef = PropertyRef("support_hours_type")
    support_hours_time_zone: PropertyRef = PropertyRef("support_hours_time_zone")
    support_hours_start_time: PropertyRef = PropertyRef("support_hours_start_time")
    support_hours_end_time: PropertyRef = PropertyRef("support_hours_end_time")
    support_hours_days_of_week: PropertyRef = PropertyRef("support_hours_days_of_week")


@dataclass(frozen=True)
class PagerDutyServiceToTeamProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyTeam)-[:ASSOCIATED_WITH]->(:PagerDutyService)
class PagerDutyServiceToTeamRel(CartographyRelSchema):
    target_node_label: str = "PagerDutyTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("teams_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: PagerDutyServiceToTeamProperties = PagerDutyServiceToTeamProperties()


@dataclass(frozen=True)
class PagerDutyServiceSchema(CartographyNodeSchema):
    label: str = "PagerDutyService"
    properties: PagerDutyServiceProperties = PagerDutyServiceProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PagerDutyServiceToTeamRel(),
        ]
    )
