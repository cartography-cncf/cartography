from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SemgrepFindingAssistantNodeProperties(CartographyNodeProperties):
    # id matches the parent finding's id (1:1 relationship)
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # autofix
    autofix_fix_code: PropertyRef = PropertyRef("autofixFixCode")
    # autotriage
    autotriage_verdict: PropertyRef = PropertyRef("autotriagedVerdict")
    autotriage_reason: PropertyRef = PropertyRef("autotriagedReason")
    # component
    component_tag: PropertyRef = PropertyRef("componentTag")
    component_risk: PropertyRef = PropertyRef("componentRisk")
    # guidance
    guidance_summary: PropertyRef = PropertyRef("guidanceSummary")
    guidance_instructions: PropertyRef = PropertyRef("guidanceInstructions")
    # rule_explanation
    rule_explanation_summary: PropertyRef = PropertyRef("ruleExplanationSummary")
    rule_explanation: PropertyRef = PropertyRef("ruleExplanation")


@dataclass(frozen=True)
class SemgrepFindingAssistantToDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepFindingAssistant)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepFindingAssistantToDeploymentRel(CartographyRelSchema):
    target_node_label: str = "SemgrepDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DEPLOYMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepFindingAssistantToDeploymentRelProperties = (
        SemgrepFindingAssistantToDeploymentRelProperties()
    )


@dataclass(frozen=True)
class SemgrepFindingAssistantSchema(CartographyNodeSchema):
    label: str = "SemgrepFindingAssistant"
    properties: SemgrepFindingAssistantNodeProperties = (
        SemgrepFindingAssistantNodeProperties()
    )
    sub_resource_relationship: SemgrepFindingAssistantToDeploymentRel = (
        SemgrepFindingAssistantToDeploymentRel()
    )
