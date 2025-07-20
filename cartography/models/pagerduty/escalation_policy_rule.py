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
class PagerDutyEscalationPolicyRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    escalation_delay_in_minutes: PropertyRef = PropertyRef(
        "escalation_delay_in_minutes", extra_index=True
    )


@dataclass(frozen=True)
class PagerDutyEscalationPolicyRuleToEscalationPolicyProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    order: PropertyRef = PropertyRef("_escalation_policy_order")


@dataclass(frozen=True)
# (:PagerDutyEscalationPolicy)-[:HAS_RULE]->(:PagerDutyEscalationPolicyRule)
class PagerDutyEscalationPolicyRuleToEscalationPolicyRel(CartographyRelSchema):
    target_node_label: str = "PagerDutyEscalationPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_escalation_policy_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULE"
    properties: PagerDutyEscalationPolicyRuleToEscalationPolicyProperties = (
        PagerDutyEscalationPolicyRuleToEscalationPolicyProperties()
    )


@dataclass(frozen=True)
class PagerDutyEscalationPolicyRuleToUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutyUser)-[:ASSOCIATED_WITH]->(:PagerDutyEscalationPolicyRule)
class PagerDutyEscalationPolicyRuleToUserRel(CartographyRelSchema):
    target_node_label: str = "PagerDutyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("users_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: PagerDutyEscalationPolicyRuleToUserProperties = (
        PagerDutyEscalationPolicyRuleToUserProperties()
    )


@dataclass(frozen=True)
class PagerDutyEscalationPolicyRuleToScheduleProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PagerDutySchedule)<-[:ASSOCIATED_WITH]-(:PagerDutyEscalationPolicyRule)
class PagerDutyEscalationPolicyRuleToScheduleRel(CartographyRelSchema):
    target_node_label: str = "PagerDutySchedule"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("schedules_id", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: PagerDutyEscalationPolicyRuleToScheduleProperties = (
        PagerDutyEscalationPolicyRuleToScheduleProperties()
    )


@dataclass(frozen=True)
class PagerDutyEscalationPolicyRuleSchema(CartographyNodeSchema):
    label: str = "PagerDutyEscalationPolicyRule"
    properties: PagerDutyEscalationPolicyRuleProperties = (
        PagerDutyEscalationPolicyRuleProperties()
    )
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        [
            PagerDutyEscalationPolicyRuleToEscalationPolicyRel(),
            PagerDutyEscalationPolicyRuleToUserRel(),
            PagerDutyEscalationPolicyRuleToScheduleRel(),
        ]
    )
