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
class PagerDutyEscalationPolicyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Escalation policy ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    html_url: PropertyRef = PropertyRef(
        "html_url", description="PagerDuty web URL for the escalation policy."
    )
    type: PropertyRef = PropertyRef(
        "type", description="PagerDuty object type for the escalation policy."
    )
    summary: PropertyRef = PropertyRef(
        "summary", description="Short summary of the escalation policy."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Escalation policy name."
    )
    on_call_handoff_notifications: PropertyRef = PropertyRef(
        "on_call_handoff_notifications",
        description="Policy for sending on-call handoff notifications.",
    )
    num_loops: PropertyRef = PropertyRef(
        "num_loops", description="Number of times the escalation policy repeats."
    )


@dataclass(frozen=True)
class PagerDutyEscalationPolicyToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyService)-[:ASSOCIATED_WITH]->(:PagerDutyEscalationPolicy)
class PagerDutyEscalationPolicyToServiceRel(CartographyRelSchema):
    """A service associated with an escalation policy."""

    target_node_label: str = "PagerDutyService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("services_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: PagerDutyEscalationPolicyToServiceRelProperties = (
        PagerDutyEscalationPolicyToServiceRelProperties()
    )


@dataclass(frozen=True)
class PagerDutyEscalationPolicyToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyTeam)-[:ASSOCIATED_WITH]->(:PagerDutyEscalationPolicy)
class PagerDutyEscalationPolicyToTeamRel(CartographyRelSchema):
    """A team associated with an escalation policy."""

    target_node_label: str = "PagerDutyTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("teams_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: PagerDutyEscalationPolicyToTeamRelProperties = (
        PagerDutyEscalationPolicyToTeamRelProperties()
    )


@dataclass(frozen=True)
class PagerDutyEscalationPolicySchema(CartographyNodeSchema):
    """A PagerDuty escalation policy for routing incidents."""

    label: str = "PagerDutyEscalationPolicy"
    properties: PagerDutyEscalationPolicyProperties = (
        PagerDutyEscalationPolicyProperties()
    )
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PagerDutyEscalationPolicyToServiceRel(),
            PagerDutyEscalationPolicyToTeamRel(),
        ]
    )
