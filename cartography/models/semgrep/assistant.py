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
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier shared with the parent finding.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # autofix
    autofix_fix_code: PropertyRef = PropertyRef(
        "autofixFixCode",
        description="AI-generated source code fix for the finding.",
    )
    # autotriage
    autotriage_verdict: PropertyRef = PropertyRef(
        "autotriagedVerdict",
        description="AI recommendation to fix or ignore the finding.",
    )
    autotriage_reason: PropertyRef = PropertyRef(
        "autotriagedReason",
        description="Reasoning supporting the AI triage verdict.",
    )
    # component
    component_tag: PropertyRef = PropertyRef(
        "componentTag",
        description="AI-generated tag describing the matched code's purpose.",
    )
    component_risk: PropertyRef = PropertyRef(
        "componentRisk",
        description="AI-assessed risk level of the affected component.",
    )
    # guidance
    guidance_summary: PropertyRef = PropertyRef(
        "guidanceSummary",
        description="Short summary explaining how to remediate the finding.",
    )
    guidance_instructions: PropertyRef = PropertyRef(
        "guidanceInstructions",
        description="Step-by-step remediation instructions.",
    )
    # rule_explanation
    rule_explanation_summary: PropertyRef = PropertyRef(
        "ruleExplanationSummary",
        description="Concise explanation of why the rule flagged the code.",
    )
    rule_explanation: PropertyRef = PropertyRef(
        "ruleExplanation",
        description="Detailed explanation of the rule and its security impact.",
    )


@dataclass(frozen=True)
class SemgrepFindingAssistantToDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepFindingAssistant)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepFindingAssistantToDeploymentRel(CartographyRelSchema):
    """Connects a Semgrep deployment to Assistant data generated for its findings."""

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
    """AI-generated triage, remediation, and explanation data for a finding."""

    label: str = "SemgrepFindingAssistant"
    properties: SemgrepFindingAssistantNodeProperties = (
        SemgrepFindingAssistantNodeProperties()
    )
    sub_resource_relationship: SemgrepFindingAssistantToDeploymentRel = (
        SemgrepFindingAssistantToDeploymentRel()
    )
