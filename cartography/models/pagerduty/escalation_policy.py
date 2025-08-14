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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    html_url: PropertyRef = PropertyRef("html_url")
    type: PropertyRef = PropertyRef("type")
    summary: PropertyRef = PropertyRef("summary")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    on_call_handoff_notifications: PropertyRef = PropertyRef(
        "on_call_handoff_notifications"
    )
    num_loops: PropertyRef = PropertyRef("num_loops")


@dataclass(frozen=True)
class PagerDutyEscalationPolicyToServiceProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyService)-[:ASSOCIATED_WITH]->(:PagerDutyEscalationPolicy)
class PagerDutyEscalationPolicyToServiceRel(CartographyRelSchema):
    target_node_label: str = "PagerDutyService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("services_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: PagerDutyEscalationPolicyToServiceProperties = (
        PagerDutyEscalationPolicyToServiceProperties()
    )


@dataclass(frozen=True)
class PagerDutyEscalationPolicyToTeamProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyTeam)-[:ASSOCIATED_WITH]->(:PagerDutyEscalationPolicy)
class PagerDutyEscalationPolicyToTeamRel(CartographyRelSchema):
    target_node_label: str = "PagerDutyTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("teams_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: PagerDutyEscalationPolicyToTeamProperties = (
        PagerDutyEscalationPolicyToTeamProperties()
    )


@dataclass(frozen=True)
class PagerDutyEscalationPolicySchema(CartographyNodeSchema):
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
