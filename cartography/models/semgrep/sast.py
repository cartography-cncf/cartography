from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SemgrepSASTFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    rule_id: PropertyRef = PropertyRef("ruleId", extra_index=True)
    repository: PropertyRef = PropertyRef("repositoryName", extra_index=True)
    repository_url: PropertyRef = PropertyRef("repositoryUrl")
    branch: PropertyRef = PropertyRef("branch")
    title: PropertyRef = PropertyRef("title", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    severity: PropertyRef = PropertyRef("severity")
    confidence: PropertyRef = PropertyRef("confidence")
    categories: PropertyRef = PropertyRef("categories")
    cwe_names: PropertyRef = PropertyRef("cweNames")
    owasp_names: PropertyRef = PropertyRef("owaspNames")
    file_path: PropertyRef = PropertyRef("filePath", extra_index=True)
    start_line: PropertyRef = PropertyRef("startLine")
    start_col: PropertyRef = PropertyRef("startCol")
    end_line: PropertyRef = PropertyRef("endLine")
    end_col: PropertyRef = PropertyRef("endCol")
    line_of_code_url: PropertyRef = PropertyRef("lineOfCodeUrl")
    state: PropertyRef = PropertyRef("state")
    fix_status: PropertyRef = PropertyRef("fixStatus")
    triage_status: PropertyRef = PropertyRef("triageStatus")
    opened_at: PropertyRef = PropertyRef("openedAt")


@dataclass(frozen=True)
class SemgrepSASTFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepSASTFindingToSemgrepDeploymentRel(CartographyRelSchema):
    target_node_label: str = "SemgrepDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DEPLOYMENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepSASTFindingToSemgrepDeploymentRelProperties = (
        SemgrepSASTFindingToSemgrepDeploymentRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSASTFindingToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)-[:FOUND_IN]->(:GitHubRepository)
class SemgrepSASTFindingToGithubRepoRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repositoryUrl")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSASTFindingToGithubRepoRelProperties = (
        SemgrepSASTFindingToGithubRepoRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSASTFindingToAssistantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSASTFinding)-[:HAS_ASSISTANT]->(:SemgrepFindingAssistant)
class SemgrepSASTFindingToAssistantRel(CartographyRelSchema):
    target_node_label: str = "SemgrepFindingAssistant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("assistantId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ASSISTANT"
    properties: SemgrepSASTFindingToAssistantRelProperties = (
        SemgrepSASTFindingToAssistantRelProperties()
    )


@dataclass(frozen=True)
class SemgrepSASTFindingSchema(CartographyNodeSchema):
    label: str = "SemgrepSASTFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityIssue"])
    properties: SemgrepSASTFindingNodeProperties = SemgrepSASTFindingNodeProperties()
    sub_resource_relationship: SemgrepSASTFindingToSemgrepDeploymentRel = (
        SemgrepSASTFindingToSemgrepDeploymentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepSASTFindingToGithubRepoRel(),
            SemgrepSASTFindingToAssistantRel(),
        ],
    )
